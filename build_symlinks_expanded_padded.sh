#!/bin/bash
# Symlinks the EXPANDED_PADDED-variant pipeline outputs into DeepPT/10metadata/.
# Mirrors build_symlinks_padded.sh but for the expanded_padded variant's
# tagged filenames.

SRC_DIR=/working/lab_quann/louiseN/BC_data/Xenium/metadata
DEST_DIR=/working/lab_quann/louiseN/DeepPT/10metadata

mkdir -p "$DEST_DIR"

FILES=(
  "AVD_61FEX_expanded_padded_pearson_zscored_fold0.csv"
  "AVD_61FEX_expanded_padded_pearson_zscored_fold1.csv"
  "AVD_61FEX_expanded_padded_genes.txt"
  "AVD_61FEX_expanded_padded_train_valid_test_idx.npz"
)

for f in "${FILES[@]}"; do
  src="$SRC_DIR/$f"
  dest="$DEST_DIR/$f"

  if [ ! -e "$src" ]; then
    echo "[MISSING] $src does not exist yet -- skipping"
    continue
  fi

  if [ -L "$dest" ] || [ -e "$dest" ]; then
    echo "[SKIP] $dest already exists -- remove it first if you want to relink"
    continue
  fi

  ln -s "$src" "$dest"
  echo "[OK] linked $dest -> $src"
done

echo ""
ls -la "$DEST_DIR" | grep expanded_padded
