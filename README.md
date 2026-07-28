## Scripts Overview (H&E-to-Expression Prediction Pipeline)

### 1. Xenium (ST) Preprocessing

| Script | Purpose |
|---|---|
| `xenium_pipeline_config.py` | Shared configuration (slide order, project name, variant paths). Imported by other scripts, not run directly. |
| `xenium_two_slide_pipeline.py` | Loads both slides' raw Xenium count matrices, drops non-gene control probes/codewords, combines slides via inner join on gene panel, applies basic filtering (min_counts, min_cells) and gene-level 3xMAD outlier removal (detection frequency and log-transformed mean expression), fits Pearson residuals per fold (train-slide-only). |
| `xenium_collect_features.py` | Pools per-cell image feature `.npy` files into one array per variant, matching against the surviving cell list. Reports cells missing a feature file (failed crop extraction). |
| `xenium_realign_and_zscore_variant.py` | Re-filters/reorders Pearson targets to match a variant's actual surviving cells, re-z-scores using train-slide-only statistics, rebuilds the train/valid/test split. |
| `build_symlinks_expanded_padded.sh` / `build_symlinks_padded.sh` | Symlinks variant-specific outputs into the DeepPT training directory structure. |

### 2. Feature Compression and Model Training

| Script | Purpose |
|---|---|
| `vectorized_model_AE.py` | Vectorized autoencoder (2048→512 dims), replacing the original DeepPT `1main_AE.py`'s per-sample loop with batched tensor operations. |
| `utils.py` | Original DeepPT dataset loader, patched (one-line fold-aware fix to load the correct fold-specific targets file). |
| `model_MLP.py` | Original DeepPT model architecture (`MLP_regression`) and result-analysis logic (`analyze_result()`), unmodified. |
| `vectorized_1main_train.py` | Vectorized training script, replacing the original `1main_train.py`'s per-sample loop with batched tensor operations. Reuses the original `MLP_regression` architecture and `analyze_result()` output logic. |
| `run_vectorized_AE_expanded_padded.sh` / `run_vectorized_AE_padded.sh` | PBS job wrappers for the AE step, per variant. |
| `run_vectorized_deeppt_train.sh` | PBS array job wrapper for training (8 tasks: 2 folds × 4 gene batches), parameterized by `VARIANT`. |
| `run_xenium_collect_features.sh` / `run_xenium_realign_and_zscore_variant.sh` / `run_xenium_two_slide_pipeline.sh` | PBS job wrappers for the corresponding Xenium preprocessing scripts. |

### 3. Result Consolidation and Analysis

| Script | Purpose |
|---|---|
| `print_all_coef_data_csv.py` | Consolidates all `coef_sorted_based_test.txt` result files (both variants, all folds/gene batches) into one `all_coef_data.csv`. |
| `print_all_loss_curve_data.py` | Consolidates all `train_valid_loss.txt` result files into one `all_loss_curve_data.csv`. |
| `analyze_variant_comparison.py` | Whole-panel comparison, top-gene overlap, and validation/test consistency between variants, computed from `all_coef_data.csv`. |
| `build_overview_scatter.py` | Generates predicted-vs-true scatter plots (`overview_scatter_*.png/.pdf`), per variant. |

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
