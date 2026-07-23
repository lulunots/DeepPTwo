import pandas as pd
import tifffile
import argparse
import os
import numpy as np
import json

def crop_per_cell(xenium_folder, margin, outloc):
    image = f"{xenium_folder}/xenium_HE_aligned/morphology_focus.ome.tif"
    cell_bounds = f"{xenium_folder}/xenium_HE_aligned/cell_boundaries.parquet"
    summary = f"{xenium_folder}/qc/summary.json"

    # input validation
    if not os.path.exists(image):
        raise FileNotFoundError(f"Image not found: {image}")
    if not os.path.exists(outloc):
        os.makedirs(outloc)

    # image loading
    im = tifffile.imread(image)
    im_name = os.path.basename(image).split('.')[0]
    if im.ndim == 3 and im.shape[0] in (1, 3, 4) and im.shape[0] < im.shape[-1]:
        im = np.moveaxis(im, 0, -1)
    im_height, im_width = im.shape[:2]

    # cell boundary file loading
    df = pd.read_parquet(cell_bounds)
    required_cols = {'cell_id', 'vertex_x', 'vertex_y'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV missing columns: {required_cols - set(df.columns)}")
    df[['vertex_x', 'vertex_y']] = df[['vertex_x', 'vertex_y']].astype(float)

    # convert mm -> pixels (pixel_size_out from qc/summary.json, in mm/pixel)
    if not os.path.exists(summary):
        raise FileNotFoundError(f"QC summary not found: {summary}")
    with open(summary) as f:
        summary_data = json.load(f)
    if "pixel_size_out" not in summary_data:
        raise KeyError(f"'pixel_size_out' missing from {summary}")
    pixel_size_out = summary_data["pixel_size_out"]
    df['vertex_x'] = df['vertex_x'] / pixel_size_out
    df['vertex_y'] = df['vertex_y'] / pixel_size_out
    
    # quick diagnostic check
    print(f"Image dims: {im_height} x {im_width}")
    print(f"Pixel x range: {df['vertex_x'].min():.1f} – {df['vertex_x'].max():.1f}")
    print(f"Pixel y range: {df['vertex_y'].min():.1f} – {df['vertex_y'].max():.1f}")
    
    result = df.groupby('cell_id').agg({'vertex_x': ['min', 'max'], 'vertex_y': ['min', 'max']})
    result.columns = ['_'.join(col) for col in result.columns.values]

    # margin calculation
    cell_margins = (((result['vertex_x_max'] - result['vertex_x_min']) + 
                     (result['vertex_y_max'] - result['vertex_y_min'])) * margin / 2).astype(int)
    
    result['cell_margin'] = cell_margins # store in the dataframe

    # register boundary conditions
    result['valid'] = ~((result['vertex_y_min'] - cell_margins < 0) |
                    (result['vertex_y_max'] + cell_margins > im_height) |
                    (result['vertex_x_min'] - cell_margins < 0) |
                    (result['vertex_x_max'] + cell_margins > im_width)) # store booleans for boundary conditions

    # filter out cells at boundary conditions
    valid = result[result['valid']] 

    if valid.empty:
        print("No valid cells to crop after boundary filtering")
        return

    skipped = len(result) - len(valid) # report skipped cells for optional debugging
    if skipped > 0:
        print(f"Skipped {skipped} cells (boundary violations)")

    for id, row in valid.iterrows():
        x_min=row['vertex_x_min']
        x_max=row['vertex_x_max']
        y_min=row['vertex_y_min']
        y_max=row['vertex_y_max']
        cell_marg = row['cell_margin']

        cropped = im[round(y_min-cell_marg):round(y_max+cell_marg), round(x_min-cell_marg):round(x_max+cell_marg)]

        tifffile.imwrite(os.path.join(outloc, f'{im_name}_{id}.ome.tif'), cropped)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='produce per cell crops from image',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'xenium_folder',
    help=(
        "Path to a sample's H&E-alignment output folder (the parent of "
        "'xenium_HE_aligned/' and 'qc/'). Expected structure:\n"
        "  <xenium_folder>/\n"
        "  ├── xenium_HE_aligned/\n"
        "  │   ├── morphology_focus.ome.tif\n"
        "  │   └── cell_boundaries.parquet\n"
        "  └── qc/\n"
        "      └── summary.json"
        )
    )
    parser.add_argument('outloc', help='output directory')
    parser.add_argument('--margin', type=float, default=0.2, help='margin factor (default: 0.2)')
    
    args = parser.parse_args()
    
    crop_per_cell(args.xenium_folder, args.margin, args.outloc)