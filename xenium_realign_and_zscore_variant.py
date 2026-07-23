"""
Variant-aware realignment: re-filter/re-order the fold-specific Pearson
targets to match a given image variant's actual surviving cell set (which
differs per variant, since different crop counts fail for different
processing pipelines), then re-z-score using that variant's train-slide
statistics, and rebuild the split file to match.

Usage:
    python xenium_realign_and_zscore_variant.py expanded_padded
    python xenium_realign_and_zscore_variant.py padded

Requires xenium_collect_features.py to have already been run for this
variant (produces {project}_{variant}_final_cell_order.csv).
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xenium_pipeline_config import SLIDE_ORDER, PROJECT, DATASET_VARIANTS

import numpy as np
import pandas as pd

if len(sys.argv) != 2 or sys.argv[1] not in DATASET_VARIANTS:
    valid = ", ".join(DATASET_VARIANTS.keys())
    raise SystemExit(f"Usage: python {sys.argv[0]} <variant>  (valid: {valid})")

variant = sys.argv[1]
outdir = "/working/lab_quann/louiseN/BC_data/Xenium/metadata"
project = PROJECT

final_order_path = f"{outdir}/{project}_{variant}_final_cell_order.csv"
final_order = pd.read_csv(final_order_path)
print(f"Variant: {variant}")
print(f"Final cell count: {len(final_order)}")
print(final_order["slide"].value_counts())

keep_cell_ids = set(final_order["cell_id"])

# ---- 1. Re-filter + re-order each fold's ORIGINAL (unscored) targets, then
#         re-z-score using THIS variant's surviving train-slide cells -------
for ik_fold, train_slide in enumerate(SLIDE_ORDER):
    src_path = f"{outdir}/{project}_pearson_fold{ik_fold}.csv"
    df = pd.read_csv(src_path)
    print(f"\nFold {ik_fold}: loaded {len(df)} rows from {src_path}")

    df = df[df["cell_id"].isin(keep_cell_ids)].copy()
    df = df.set_index("cell_id").loc[final_order["cell_id"]].reset_index()

    assert list(df["cell_id"]) == list(final_order["cell_id"]), \
        f"Fold {ik_fold}: row order mismatch after realignment!"

    gene_cols = [c for c in df.columns if c not in ("cell_id", "slide")]

    # re-z-score using THIS variant's train-slide-only cells (counts differ
    # slightly per variant since different crops failed)
    train_mask = df["slide"] == train_slide
    n_train = train_mask.sum()
    print(f"  train-slide ({train_slide}) rows after realignment: {n_train}")

    train_vals = df.loc[train_mask, gene_cols].values
    gene_mean = train_vals.mean(axis=0)
    gene_std = train_vals.std(axis=0)
    gene_std[gene_std == 0] = 1.0

    df_z = df.copy()
    df_z[gene_cols] = (df[gene_cols].values - gene_mean) / gene_std

    out_path = f"{outdir}/{project}_{variant}_pearson_zscored_fold{ik_fold}.csv"
    df_z.to_csv(out_path, index=False)
    print(f"  Saved: {out_path}  shape={df_z.shape}")

    stats_path = f"{outdir}/{project}_{variant}_gene_zscore_stats_fold{ik_fold}.csv"
    pd.DataFrame({"gene": gene_cols, "mean": gene_mean, "std": gene_std}).to_csv(stats_path, index=False)

# ---- 2. Rebuild the split .npz using this variant's final_position values -
N_INNER_FOLDS = 5
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

train_idx_all, valid_idx_all, test_idx_all = [], [], []

for ik_fold, train_slide in enumerate(SLIDE_ORDER):
    test_slide = [s for s in SLIDE_ORDER if s != train_slide][0]

    train_positions = final_order.loc[final_order["slide"] == train_slide, "final_position"].values.copy()
    test_positions = final_order.loc[final_order["slide"] == test_slide, "final_position"].values.copy()

    rng.shuffle(train_positions)
    inner_splits = np.array_split(train_positions, N_INNER_FOLDS)

    fold_train_list, fold_valid_list = [], []
    for il_fold in range(N_INNER_FOLDS):
        valid_positions = inner_splits[il_fold]
        train_pos = np.concatenate([inner_splits[k] for k in range(N_INNER_FOLDS) if k != il_fold])
        fold_train_list.append(train_pos)
        fold_valid_list.append(valid_positions)

    train_idx_all.append(fold_train_list)
    valid_idx_all.append(fold_valid_list)
    test_idx_all.append(test_positions)

    print(f"\nik_fold={ik_fold}: train_slide={train_slide}, test_slide={test_slide}")
    print(f"  train slide total: {len(train_positions)}, test slide total: {len(test_positions)}")

train_idx_arr = np.array(train_idx_all, dtype=object)
valid_idx_arr = np.array(valid_idx_all, dtype=object)
test_idx_arr = np.array(test_idx_all, dtype=object)

split_path = f"{outdir}/{project}_{variant}_train_valid_test_idx.npz"
np.savez(split_path, train_idx=train_idx_arr, valid_idx=valid_idx_arr, test_idx=test_idx_arr)
print(f"\nSaved: {split_path}")

# ---- 3. genes.txt is identical across variants (image processing doesn't
#         change which genes exist) -- symlink rather than duplicate --------
genes_src = f"{outdir}/{project}_genes.txt"
genes_dest = f"{outdir}/{project}_{variant}_genes.txt"
if not os.path.exists(genes_dest) and os.path.exists(genes_src):
    os.symlink(genes_src, genes_dest)
    print(f"Symlinked: {genes_dest} -> {genes_src}")

print(f"\nDone. Use project='{project}_{variant}' in load_dataset() calls for this variant.")
