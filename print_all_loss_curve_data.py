import os
import numpy as np

BASE = "/working/lab_quann/louiseN/DeepPT/13DeepPT_train/results"
variants = ["expanded_padded", "padded"]
gene_batches = [0, 56, 112, 168]

print("variant,ik_fold,i_gene_min,epoch,train_loss,valid_loss,train_coef,valid_coef,train_slope,valid_slope")

for variant in variants:
    project = f"AVD_61FEX_{variant}"

    for ik_fold in [0, 1]:
        for i_gene_min in gene_batches:
            path = f"{BASE}/{project}/result_{ik_fold}_0_{i_gene_min}/train_valid_loss.txt"
            if not os.path.exists(path):
                continue

            curve = np.loadtxt(path)
            for epoch, row in enumerate(curve):
                train_loss, valid_loss, train_coef, valid_coef, train_slope, valid_slope = row
                print(f"{variant},{ik_fold},{i_gene_min},{epoch},"
                      f"{train_loss},{valid_loss},{train_coef},{valid_coef},"
                      f"{train_slope},{valid_slope}")
