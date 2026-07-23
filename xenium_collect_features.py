"""
Collect per-cell .npy feature files (from new_simplified_feature_extraction.py)
into the single pooled {project}_{variant}_features.npy that vectorized_model_AE.py
/ 1main_AE.py expects: an object array of (cell_id, features[1, 2048]) tuples.

Supports multiple image-processing variants (e.g. "expanded_padded", "padded")
sharing the same underlying cell list (AVD_61FEX_cell_positions.csv) but coming
from differently-processed crops. Pass the variant name as a command-line arg.

Usage:
    python xenium_collect_features.py expanded_padded
    python xenium_collect_features.py padded

Only includes cells that are BOTH:
  (a) in AVD_61FEX_cell_positions.csv (survived Xenium QC/outlier filtering)
  (b) have an existing .npy feature file for this variant (some crops fail
      color normalization and are logged/skipped during extraction)

CRITICAL: if any cells are missing a feature file, this script produces a
NEW final cell order (variant-specific) that both the features file AND the
targets CSVs must share. Run xenium_realign_targets.py afterward to
re-filter/re-save the fold0/fold1 targets CSVs and the split .npz to match.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xenium_pipeline_config import PROJECT, DATASET_VARIANTS, SLIDE_NAMING

if len(sys.argv) != 2 or sys.argv[1] not in DATASET_VARIANTS:
    valid = ", ".join(DATASET_VARIANTS.keys())
    raise SystemExit(f"Usage: python {sys.argv[0]} <variant>  (valid: {valid})")

variant = sys.argv[1]
variant_cfg = DATASET_VARIANTS[variant]

if variant_cfg["features_folder"] == "REPLACE_ME":
    raise SystemExit(
        f"features_folder for variant '{variant}' is still a placeholder — "
        f"fill in the real path in xenium_pipeline_config.py before running."
    )

outdir = "/working/lab_quann/louiseN/BC_data/Xenium/metadata"
project = PROJECT

features_folder = variant_cfg["features_folder"]
FEATURE_SUFFIX = variant_cfg["suffix"]
ae_input_dir = "/working/lab_quann/louiseN/DeepPT/11slide_processing/"

print(f"Running feature collection for variant: {variant}")
print(f"  features_folder: {features_folder}")
print(f"  suffix: {FEATURE_SUFFIX}")

# ---- 1. Load the cell list that survived Xenium QC -------------------------
cell_positions = pd.read_csv(f"{outdir}/{project}_cell_positions.csv")
print(f"\nCells in cell_positions.csv (post Xenium QC): {len(cell_positions)}")

# ---- 2. Check which cells have an existing feature file --------------------
def cell_id_to_feature_filename(cell_id):
    slide, barcode = cell_id.split("_", 1)
    naming = SLIDE_NAMING.get(slide, "plain")
    if naming == "bytes_repr":
        return f"{slide}_b'{barcode}'{FEATURE_SUFFIX}"
    else:
        return f"{cell_id}{FEATURE_SUFFIX}"


has_feature = []
feature_filenames = []
for cell_id in cell_positions["cell_id"]:
    fname = cell_id_to_feature_filename(cell_id)
    npy_path = os.path.join(features_folder, f"{fname}.npy")
    has_feature.append(os.path.exists(npy_path))
    feature_filenames.append(fname)

cell_positions["feature_filename"] = feature_filenames
cell_positions["has_feature"] = has_feature
n_missing = (~cell_positions["has_feature"]).sum()

print(f"Cells with a feature .npy present: {cell_positions['has_feature'].sum()}")
print(f"Cells MISSING a feature file: {n_missing}")

if n_missing > 0:
    print(f"\n[WARNING] {n_missing} cells are missing feature files for variant "
          f"'{variant}' — check {features_folder}_failed_crops.txt. These cells "
          f"will be DROPPED from the final dataset for this variant, and the "
          f"targets CSVs / split file will need to be re-aligned to match — "
          f"run xenium_realign_targets.py next.")
    missing_ids = cell_positions.loc[~cell_positions["has_feature"], "cell_id"]
    missing_log = f"{outdir}/{project}_{variant}_cells_missing_features.txt"
    missing_ids.to_csv(missing_log, index=False, header=False)
    print(f"Saved list of missing cell_ids: {missing_log}")

# ---- 3. Build the final cell list (intersection), fixed deterministic order
final_cells = cell_positions[cell_positions["has_feature"]].copy()
final_cells = final_cells.sort_values("row_position").reset_index(drop=True)
final_cells["final_position"] = np.arange(len(final_cells))

print(f"\nFinal aligned cell count ({variant}): {len(final_cells)}")
print(final_cells["slide"].value_counts())

# ---- 4. Assemble the pooled features array in this exact order -------------
features_list = []
for cell_id, fname in zip(final_cells["cell_id"], final_cells["feature_filename"]):
    npy_path = os.path.join(features_folder, f"{fname}.npy")
    feat = np.load(npy_path)  # shape (1, 2048)
    features_list.append((cell_id, feat))  # keep the CLEAN cell_id, not the ugly filename

features_array = np.array(features_list, dtype=object)

if not os.path.exists(ae_input_dir):
    os.makedirs(ae_input_dir)

# variant-tagged output filename so multiple variants can coexist without
# overwriting each other -- pass project="AVD_61FEX_{variant}" to
# vectorized_model_AE.py / 1main_AE.py to match this naming
out_project = f"{project}_{variant}"
out_path = os.path.join(ae_input_dir, f"{out_project}_features.npy")
np.save(out_path, features_array)
print(f"\nSaved: {out_path}  ({len(features_array)} entries)")

# ---- 5. Save the final cell order — needed to re-align targets next -------
final_order_path = f"{outdir}/{project}_{variant}_final_cell_order.csv"
final_cells[["final_position", "cell_id", "slide", "row_position"]].to_csv(
    final_order_path, index=False
)
print(f"Saved final cell order mapping: {final_order_path}")

if n_missing > 0:
    print(f"\nNEXT STEP REQUIRED: run xenium_realign_targets.py (pointed at "
          f"variant='{variant}') to re-filter/re-save the targets CSVs and "
          f"split .npz to match this final order.")
else:
    print(f"\nNo missing features for '{variant}' — targets CSVs and split "
          f".npz already match this order, no realignment needed.")
