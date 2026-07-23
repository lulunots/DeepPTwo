"""
Two-slide Xenium pipeline for cross-slide train/test evaluation.

Slides:
  4851A = AVD_61FEX_4851A (Lymph Node, LumA, Left Axillary)
  5626A = AVD_61FEX_5626A (Lymph Node, LumB, Left Axillary)

Design (as agreed):
  - gene-level 3xMAD outlier removal computed on COMBINED data (both slides)
    -> guarantees both slides end up with the same gene panel
  - cell-level 3xMAD outlier removal computed PER SLIDE
    -> QC thresholds can legitimately differ by slide/batch
  - Pearson residual model fit ONLY on the training slide, per fold, then
    applied to both slides using train-derived per-gene proportions
    -> avoids leaking test-slide statistics into the transform

IMPORTANT STRUCTURAL NOTE:
Because the Pearson fit differs per fold (fold 0 fits on 4851A, fold 1 fits
on 5626A), this produces TWO separate targets CSVs, not one shared file.
DeepPT's load_dataset() as written expects a single
"{project}_{rna_type}.csv" for all folds. You'll need a one-line patch to
utils.py's load_dataset() to make rna_file fold-aware, e.g.:

    rna_file = f"{path2target}{project}_{rna_type}_fold{ik_fold}.csv"

This script saves files matching that pattern.
"""

import numpy as np
import pandas as pd
import scanpy as sc
import anndata as ad
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xenium_pipeline_config import SLIDE_ORDER, PROJECT

# ---- paths — update to your actual HPC paths -------------------------------
paths = {
    SLIDE_ORDER[0]: "/working/lab_quann/louiseN/BC_data/Xenium/metadata/4851A/cell_feature_matrix",
    SLIDE_ORDER[1]: "/working/lab_quann/louiseN/BC_data/Xenium/metadata/5626A/cell_feature_matrix",
}
outdir = "/working/lab_quann/louiseN/BC_data/Xenium/metadata"
project = PROJECT  # was hardcoded "AVD_61FEX" — now sourced from xenium_pipeline_config.py


def mad_outlier_mask(values, n_mads=3):
    """Two-sided outlier flag: True where value is >n_mads MADs from median."""
    median = np.median(values)
    mad = np.median(np.abs(values - median))
    if mad == 0:
        return np.zeros(len(values), dtype=bool)
    modified_z = np.abs(values - median) / mad
    return modified_z > n_mads


def fit_and_transform_pearson(adata_all, train_mask, theta=100.0):
    """
    Analytic Pearson residuals, fit ONLY on cells where train_mask is True,
    then applied to ALL cells (train_mask True or False) using each cell's
    own total count as size factor but train-derived per-gene proportions.

    This mirrors scanpy's normalize_pearson_residuals formula:
        mu_ij = n_i * pi_j          (pi_j = gene j's share of total counts)
        residual_ij = (y_ij - mu_ij) / sqrt(mu_ij + mu_ij^2 / theta)
    but computes pi_j from train cells only, avoiding test-slide leakage.
    theta=100 matches scanpy's own fixed default (not per-gene fitted).
    """
    X = adata_all.layers["counts"]
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)

    X_train = X[train_mask]
    n_train_total = X_train.sum()
    gene_sums_train = X_train.sum(axis=0)
    pi_j = gene_sums_train / n_train_total  # gene proportions, TRAIN ONLY

    n_i = X.sum(axis=1)  # each cell's own total count (train or test)
    mu = np.outer(n_i, pi_j)  # expected counts under train-fit model

    residuals = (X - mu) / np.sqrt(mu + (mu ** 2) / theta)

    # clip using train set size, consistent with the train-only fit
    clip_val = np.sqrt(train_mask.sum())
    residuals = np.clip(residuals, -clip_val, clip_val)

    return residuals, clip_val


# ---- 1. Load both slides, tag with slide id, concatenate -------------------
adatas = []
for slide_name, path in paths.items():
    a = sc.read_10x_mtx(path, var_names="gene_symbols", cache=True)
    a = a[:, a.var["feature_types"] == "Gene Expression"].copy()
    a.obs["slide"] = slide_name
    # make barcodes unique across slides
    a.obs_names = [f"{slide_name}_{bc}" for bc in a.obs_names]
    adatas.append(a)
    print(f"{slide_name}: loaded {a.shape[0]} cells x {a.shape[1]} genes")

adata = ad.concat(adatas, join="inner", index_unique=None)
# NOTE: inner join (intersection) is deliberate here, not a default fallback.
# 4851A used the base 280-gene "Xenium Human Breast Gene Expression" panel;
# 5626A used that same base panel plus a custom 100-gene add-on module
# (breast-cancer/DNA-repair pathway genes — AKT1, BRCA1, BRCA2, AURKA, etc.).
# Inner join keeps only the shared base-panel genes and explicitly EXCLUDES
# the add-on genes, since they were never measured on 4851A and can't be
# evaluated across both slides of the train/test split.
print(f"\nCombined gene panel (base-panel genes only, add-ons excluded): {adata.shape[1]}")
print(f"\nCombined: {adata.shape[0]} cells x {adata.shape[1]} genes")

# ---- 2. Basic filtering (combined) ------------------------------------------
sc.pp.filter_cells(adata, min_counts=10)
sc.pp.filter_genes(adata, min_cells=5)
adata.layers["counts"] = adata.X.copy()
print(f"After basic filtering: {adata.shape[0]} cells x {adata.shape[1]} genes")

# ---- 3. GENE outlier removal via 3xMAD — on COMBINED data ------------------
X_counts = adata.layers["counts"]
X_counts = X_counts.toarray() if hasattr(X_counts, "toarray") else np.asarray(X_counts)
gene_names = adata.var_names.to_numpy()
n_cells_total = X_counts.shape[0]

detection_freq = np.zeros(len(gene_names))
mean_nonzero_expr = np.zeros(len(gene_names))
for j in range(X_counts.shape[1]):
    nz = X_counts[:, j][X_counts[:, j] > 0]
    detection_freq[j] = len(nz) / n_cells_total
    mean_nonzero_expr[j] = nz.mean() if len(nz) > 0 else 0

log_mean_expr = np.log1p(mean_nonzero_expr)
freq_outlier = mad_outlier_mask(detection_freq, n_mads=3)
expr_outlier = mad_outlier_mask(log_mean_expr, n_mads=3)
gene_outlier = freq_outlier | expr_outlier

print(f"\nGene outliers via 3xMAD (combined slides): {gene_outlier.sum()} / {len(gene_names)} flagged")

adata = adata[:, ~gene_outlier].copy()
print(f"Genes remaining: {adata.shape[1]}")

# ---- 4. CELL outlier removal via 3xMAD — PER SLIDE -------------------------
sc.pp.calculate_qc_metrics(adata, inplace=True, percent_top=None, log1p=True)

keep_mask = np.ones(adata.shape[0], dtype=bool)
for slide_name in paths.keys():
    slide_mask = (adata.obs["slide"] == slide_name).values
    total_out = mad_outlier_mask(adata.obs["log1p_total_counts"].values[slide_mask], n_mads=3)
    genes_out = mad_outlier_mask(adata.obs["log1p_n_genes_by_counts"].values[slide_mask], n_mads=3)
    slide_outlier = total_out | genes_out

    slide_idx = np.where(slide_mask)[0]
    keep_mask[slide_idx[slide_outlier]] = False
    print(f"\n{slide_name}: {slide_outlier.sum()} / {slide_mask.sum()} cells flagged as outliers")

adata = adata[keep_mask].copy()
print(f"\nCells remaining after per-slide outlier removal: {adata.shape[0]}")
print(adata.obs["slide"].value_counts())

# ---- 5. Fold-specific Pearson residuals (fit on train slide only) ---------
slide_names = SLIDE_ORDER  # explicit single source of truth, not dict insertion order
assert set(slide_names) == set(paths.keys()), \
    f"SLIDE_ORDER {slide_names} doesn't match paths keys {list(paths.keys())}"
genes = adata.var_names.tolist()
cell_ids = adata.obs_names.tolist()
slide_labels = adata.obs["slide"].values

for ik_fold, train_slide in enumerate(slide_names):
    test_slide = [s for s in slide_names if s != train_slide][0]
    train_mask = (slide_labels == train_slide)

    print(f"\n--- Fold {ik_fold}: train={train_slide}, test={test_slide} ---")
    residuals, clip_val = fit_and_transform_pearson(adata, train_mask, theta=100.0)
    print(f"Fit on {train_mask.sum()} train cells, clip=+/-{clip_val:.2f}")
    print(f"Residual range: min={residuals.min():.2f}, max={residuals.max():.2f}")

    df = pd.DataFrame(residuals, columns=genes)
    df.insert(0, "cell_id", cell_ids)
    df.insert(1, "slide", slide_labels)

    target_path = f"{outdir}/{project}_pearson_fold{ik_fold}.csv"
    df.to_csv(target_path, index=False)
    print(f"Saved: {target_path}  shape={df.shape}")

# ---- 6. Save genes.txt (same gene panel for both folds) --------------------
counts_final = adata.layers["counts"]
counts_final = counts_final.toarray() if hasattr(counts_final, "toarray") else np.asarray(counts_final)
mean_counts = counts_final.mean(axis=0)
genes_arr = np.column_stack([genes, mean_counts.astype(str)])
genes_path = f"{outdir}/{project}_genes.txt"
np.savetxt(genes_path, genes_arr, fmt="%s")
print(f"\nSaved genes file: {genes_path}  n_genes={len(genes)}")

# ---- 7. Save cell_id -> row-position + slide mapping, for building the split
mapping_path = f"{outdir}/{project}_cell_positions.csv"
pd.DataFrame({
    "row_position": np.arange(len(cell_ids)),
    "cell_id": cell_ids,
    "slide": slide_labels,
}).to_csv(mapping_path, index=False)
print(f"Saved cell position mapping: {mapping_path}")
print("\nNext: build AVD_61FEX_train_valid_test_idx.npz using this position "
      "mapping — train_idx[0]/test_idx[0] = 4851A/5626A row positions, "
      "train_idx[1]/test_idx[1] = 5626A/4851A row positions (with il_fold "
      "splitting the training slide further for validation).")
