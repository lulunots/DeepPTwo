# scH2ST

Benchmark pipeline for spatial transcriptomics (Xenium) and H&E image alignment/feature extraction.

## Contents
- Alignment scripts (`4851_align.sh`, `5626_align.sh`, `xenium_realign_and_zscore_variant.py`)
- Cell cropping/padding pipeline (`cell_cropping/`, `cell_padding/`, `cell_expanding_and_padding/`)
- Feature extraction (`xenium_collect_features.py`)
- Model training (`vectorized_1main_train.py`, `vectorized_model_AE.py`, `model_MLP.py`)
- Analysis/plotting (`build_overview_scatter.py`, `analyze_variant_comparison.py`)

## Notes
Large intermediate outputs (`padded_result_*`, `expanded_padded_result_*`) and the container image (`xenium_he_pipeline.sif`) are excluded from this repo due to size — see `.gitignore`.

model\_MLP.py, utils\_color\_norm.py, and utils\_preprocessing.py are unmodified files from the original DeepPT codebase (Hoang et al., Nature Cancer 2024, Zenodo record 11125591), included here for reproducibility. A US patent application (No. 63/349,829) covers the original model and code; usage here is for non-commercial academic research
