import tifffile
import matplotlib.pyplot as plt
import os
import random

crop_folder = "/working/lab_quann/louiseN/benchmark/deeppt/segmented/5626A"
num_samples = 20

# Get all crop files
crop_files = [f for f in os.listdir(crop_folder) if f.endswith('.ome.tif')]
print(f"Total crops: {len(crop_files)}")

# Random sample
sample = random.sample(crop_files, min(num_samples, len(crop_files)))

# Create grid (5 cols × 4 rows for 20)
cols = 5
rows = (len(sample) + cols - 1) // cols
fig, axes = plt.subplots(rows, cols, figsize=(16, 12))
axes = axes.flatten()

# Plot
for idx, file in enumerate(sample):
    img = tifffile.imread(os.path.join(crop_folder, file))
    h, w = img.shape[:2]
    
    axes[idx].imshow(img, interpolation='nearest')
    cell_id = file.split('_')[-1].replace('.ome.tif', '')
    axes[idx].set_title(f"{cell_id}\n{w}×{h}px", fontsize=8)
    axes[idx].axis('off')

# Hide unused subplots
for idx in range(len(sample), len(axes)):
    axes[idx].axis('off')

plt.tight_layout()
plt.savefig('/tmp/crop_sample.png', dpi=100, bbox_inches='tight')
print("Saved to /tmp/crop_sample.png")
plt.show()
