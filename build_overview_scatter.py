"""
Build one combined overview scatter plot per variant: predicted vs true
expression, pooled across all 4 gene batches, colored by fold (which
slide was train vs test) -- rather than DeepPT's original one-tiny-plot-
per-gene approach.

Each fold's raw test_labels/test_preds is huge (300k+ cells x 56 genes),
so we randomly subsample per fold to keep the plot readable.

Usage:
    python build_overview_scatter.py expanded_padded
    python build_overview_scatter.py padded
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed, just save to file
import matplotlib.pyplot as plt

if len(sys.argv) != 2:
    raise SystemExit(f"Usage: python {sys.argv[0]} <variant>")

variant = sys.argv[1]
project = f"AVD_61FEX_{variant}"
results_dir = f"/working/lab_quann/louiseN/DeepPT/13DeepPT_train/results/{project}"

N_POINTS_PER_FOLD = 5000  # subsampled (cell, gene) points per fold, across all 4 gene batches
RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

fold_colors = {0: "tab:blue", 1: "tab:orange"}
fold_labels = {0: "Fold 0 (train=4851A, test=5626A)", 1: "Fold 1 (train=5626A, test=4851A)"}

gene_batches = [0, 56, 112, 168]

fig, ax = plt.subplots(figsize=(7, 7))

overall_true = []
overall_pred = []

for ik_fold in [0, 1]:
    fold_true = []
    fold_pred = []

    for i_gene_min in gene_batches:
        folder = f"{results_dir}/result_{ik_fold}_0_{i_gene_min}"
        labels_path = f"{folder}/test_labels.txt"
        preds_path = f"{folder}/test_preds.txt"

        if not (os.path.exists(labels_path) and os.path.exists(preds_path)):
            print(f"[skip] missing files in {folder}")
            continue

        labels = np.loadtxt(labels_path)  # [n_cells, 56]
        preds = np.loadtxt(preds_path)

        flat_true = labels.flatten()
        flat_pred = preds.flatten()

        # subsample from this batch's flattened points
        n_available = len(flat_true)
        n_take = min(N_POINTS_PER_FOLD // len(gene_batches), n_available)
        idx = rng.choice(n_available, size=n_take, replace=False)

        fold_true.append(flat_true[idx])
        fold_pred.append(flat_pred[idx])
        print(f"fold={ik_fold}, i_gene_min={i_gene_min}: sampled {n_take} points "
              f"from {labels.shape[0]} cells x {labels.shape[1]} genes")

    fold_true = np.concatenate(fold_true)
    fold_pred = np.concatenate(fold_pred)

    overall_true.append(fold_true)
    overall_pred.append(fold_pred)

    ax.scatter(fold_true, fold_pred, s=4, alpha=0.3,
               color=fold_colors[ik_fold], label=fold_labels[ik_fold])

overall_true = np.concatenate(overall_true)
overall_pred = np.concatenate(overall_pred)
overall_r = np.corrcoef(overall_true, overall_pred)[0, 1]

# reference y=x line
lims = [min(overall_true.min(), overall_pred.min()), max(overall_true.max(), overall_pred.max())]
ax.plot(lims, lims, "k--", linewidth=1, label="y = x (perfect prediction)")

ax.set_xlabel("True expression (Pearson residual, z-scored)")
ax.set_ylabel("Predicted expression")
ax.set_title(f"{variant}: predicted vs true expression (all genes, both folds)\n"
             f"overall R = {overall_r:.3f}, n = {len(overall_true)} sampled points")
ax.legend(loc="upper left", fontsize=8)
ax.set_aspect("equal", adjustable="box")

plt.tight_layout()
out_path = f"{results_dir}/overview_scatter_{variant}.png"
plt.savefig(out_path, dpi=150)
print(f"\nSaved: {out_path}")

out_pdf = f"{results_dir}/overview_scatter_{variant}.pdf"
plt.savefig(out_pdf)
print(f"Saved: {out_pdf}")
