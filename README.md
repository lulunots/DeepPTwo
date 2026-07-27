## Scripts Overview

### 1. Xenium (ST) Preprocessing

| Script | Purpose |
|---|---|
| `xenium_pipeline_config.py` | Shared configuration (slide order, project name, variant paths). Imported by other scripts, not run directly. |
| `xenium_two_slide_pipeline.py` | Loads both slides' raw Xenium count matrices, drops non-gene control probes/codewords, combines slides via inner join on gene panel, applies basic filtering (min_counts, min_cells) and gene-level 3xMAD outlier removal, fits Pearson residuals per fold (train-slide-only). |
| `xenium_collect_features.py` | Pools per-cell image feature `.npy` files into one array per variant, matching against the surviving cell list. Reports cells missing a feature file (failed crop extraction). |
| `xenium_realign_and_zscore_variant.py` | Re-filters/reorders Pearson targets to match a variant's actual surviving cells, re-z-scores using train-slide-only statistics, rebuilds the train/valid/test split. |
| `build_symlinks_expanded_padded.sh` / `build_symlinks_padded.sh` | Symlinks variant-specific outputs into the DeepPT training directory structure. |

### 2. Feature Compression and Model Training

| Script | Purpose |
|---|---|
| `vectorized_model_AE.py` | Vectorized autoencoder (2048→512 dims), replacing the original DeepPT `1main_AE.py`'s per-sample loop with batched tensor operations. |
| `utils.py` | Original DeepPT dataset loader, patched (one-line fold-aware fix to load the correct fold-specific targets file). |
| `model_MLP.py`, `utils_color_norm.py`, `utils_preprocessing.py` | Original DeepPT code, unmodified — model architecture, result analysis, and image preprocessing helpers. |
| `vectorized_1main_train.py` | Vectorized training script, replacing the original `1main_train.py`'s per-sample loop. Reuses the original `MLP_regression` architecture and `analyze_result()` output logic. |
| `run_vectorized_AE_expanded_padded.sh` / `run_vectorized_AE_padded.sh` | PBS job wrappers for the AE step, per variant. |
| `run_vectorized_deeppt_train.sh` | PBS array job wrapper for training (8 tasks: 2 folds × 4 gene batches), parameterized by `VARIANT`. |

### 3. Result Consolidation

| Script | Purpose |
|---|---|
| `print_all_coef_data_csv.py` | Consolidates all 16 `coef_sorted_based_test.txt` files (2 variants × 8 fold/gene-batch combinations) into one `all_coef_data.csv`. |
| `print_all_loss_curve_data.py` | Consolidates all 16 `train_valid_loss.txt` files into one `all_loss_curve_data.csv`. |
| `analyze_variant_comparison.py` | Whole-panel comparison, top-gene overlap, and validation/test consistency between variants, computed from `all_coef_data.csv`. |

### 4. Gene-Level Analysis and Tables

| Script | Purpose |
|---|---|
| `build_slide_tables.py` | Per-test-slide gene tables (expanded_padded vs. padded side by side), using a threshold-based inclusion rule. |
| `build_combined_gene_table.py` / `build_abundance_ranked_table.py` | Combined and abundance-ranked gene tables, joining correlation data with gene abundance (`AVD_61FEX_genes.txt`). |

### 5. Per-Cell and Variant Comparison Analysis

| Script | Purpose |
|---|---|
| `plot_percell_correlation.py` | Computes per-cell Pearson correlation (across all 224 genes) for a single variant, plots a fold-colored histogram. |
| `plot_percell_variant_comparison.py` | Computes per-cell correlation for both variants, produces the fold-colored histogram (two-panel) and test-slide-split violin plot comparisons. |
| `wilcoxon_paired_test.py` | Paired Wilcoxon signed-rank test comparing per-cell correlation between variants, matched by real cell ID (via `final_cell_order.csv`) rather than row position. Reports the matched-pairs rank-biserial effect size alongside the p-value. |

### 6. Overdispersion and Filtering Justification

| Script | Purpose |
|---|---|
| `plot_global_count_distribution_nb_fit.py` | Histogram of raw transcript counts (all genes × all cells), demonstrating overdispersion relative to Poisson. |
| `plot_mean_variance_before_after_3xmad.py` | Per-gene mean-variance relationship before and after 3xMAD gene outlier removal, replicating the real combined two-slide filtering logic. |

### 7. Factors Influencing Predictive Performance

| Script | Purpose |
|---|---|
| `plot_abundance_vs_accuracy.py` | Per-gene mean raw transcript abundance vs. mean gPCC, per variant, with fitted trend line and Pearson correlation. |
| `plot_variance_vs_accuracy.py` | Supplementary consistency check: per-gene expression variance vs. mean gPCC, per variant. |

### 8. Biological Interpretation

| Script / File | Purpose |
|---|---|
| `enrichr_results_organized.txt` | Consolidated Enrichr (PanglaoDB Augmented 2021) cell-type enrichment results for top/bottom 20 gene lists, across both variants and both test slides. |
| `plot_enrichr_dotplot.py` | Combined dot-plot visualizing cell-type enrichment for top- vs. bottom-ranked genes, across all 4 variant × test-slide contexts. |

## Notes
Large intermediate outputs (`padded_result_*`, `expanded_padded_result_*`) and the container image (`xenium_he_pipeline.sif`) are excluded from this repo due to size — see `.gitignore`.

model\_MLP.py, utils\_color\_norm.py, and utils\_preprocessing.py are unmodified files from the original DeepPT codebase (Hoang et al., Nature Cancer 2024, Zenodo record 11125591), included here for reproducibility. A US patent application (No. 63/349,829) covers the original model and code; usage here is for non-commercial academic research

## Licensing and provenance

This repository adapts the DeepPT framework (Hoang et al., *Nature Cancer*
5:1305–1317, 2024) to single-cell-resolution gene expression prediction.

Several scripts here are **modified versions of DeepPT source files** —
including the preprocessing, autoencoder, dataset loader (`utils.py`), and
training (`main_train.py`) scripts. These remain subject to DeepPT's original
non-commercial academic research license, and are redistributed here on that
basis. A US patent application (No. 63/349,829) covers the original model and
code. Modified files are marked as such in their headers.

Scripts written from scratch for this project (image preprocessing, cell-tile
extraction, ST preprocessing, evaluation and figure generation) are original
work produced during a research internship at the Genomics and Machine
Learning Lab, QIMR Berghofer. Licensing terms for these are pending
institutional confirmation. Until then, they are made available for
non-commercial academic research use only.

Anyone wishing to use this code beyond non-commercial academic research should
contact the DeepPT authors regarding the upstream license and patent, and the
GML Lab regarding this adaptation.

**No patient data is included in this repository.** The H&E and 10x Xenium
data analysed in the accompanying report are not redistributed here.

## Citation

If this work is useful to you, please cite the accompanying report and the
original DeepPT publication:

> Hoang, D.T., Dinstag, G., Shulman, E.D., et al. A deep-learning framework to
> predict cancer treatment response from histopathology images through imputed
> transcriptomics. *Nature Cancer* 5, 1305–1317 (2024).
