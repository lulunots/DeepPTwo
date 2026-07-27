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
