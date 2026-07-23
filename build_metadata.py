import os
import pandas as pd
import argparse

def build_metadata(folder_path, output_file, file_extension='.tif'):
    """
    Build a metadata CSV file for all slides in a folder.
    
    Args:
        folder_path: Path to folder containing slide files
        output_file: Path to output CSV file
        file_extension: File extension to filter by (default: '.tif')
    """
    
    # Validate folder exists
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # Get all files matching extension
    files = [f for f in os.listdir(folder_path) 
             if f.endswith(file_extension) and os.path.isfile(os.path.join(folder_path, f))]
    
    if not files:
        print(f"No files found with extension '{file_extension}' in {folder_path}")
        return
    
    # Sort for consistency
    files.sort()
    
    # Create metadata dataframe
    slide_names = [os.path.splitext(f)[0] for f in files]
    
    df = pd.DataFrame({
        'slide_file_name': files,
        'slide_name': slide_names
    })
    
    # Write to CSV
    df.to_csv(output_file, index=False)
    
    print(f"Metadata file created: {output_file}")
    print(f"Total slides: {len(df)}")
    print(f"\nFirst few rows:")
    print(df.head())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Build metadata CSV for slides in a folder')
    parser.add_argument('folder', help='Path to folder containing slide files')
    parser.add_argument('--output', '-o', default='metadata.csv', help='Output CSV file (default: metadata.csv)')
    parser.add_argument('--extension', '-e', default='.tif', help='File extension to filter by (default: .tif)')
    
    args = parser.parse_args()
    
    build_metadata(args.folder, args.output, args.extension)