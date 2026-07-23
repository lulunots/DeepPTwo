"""
Consolidate all 16 coef_sorted_based_test.txt files (2 variants x 8
fold/gene-batch combos) into one clean CSV, printed to stdout.

Usage:
    python print_all_coef_data_csv.py

Each result file already has valid_coef AND test_coef as separate
columns (no need for the separate _valid file).
"""

import os

BASE = "/working/lab_quann/louiseN/DeepPT/13DeepPT_train/results"
variants = ["expanded_padded", "padded"]
gene_batches = [0, 56, 112, 168]

fold_test_n = {0: 319647, 1: 371411}

print("variant,ik_fold,i_gene_min,gene,valid_coef,test_coef,valid_slope,test_slope,test_n")

for variant in variants:
    project = f"AVD_61FEX_{variant}"

    for ik_fold in [0, 1]:
        for i_gene_min in gene_batches:
            path = f"{BASE}/{project}/result_{ik_fold}_0_{i_gene_min}/coef_sorted_based_test.txt"
            if not os.path.exists(path):
                continue

            with open(path) as f:
                for line in f:
                    parts = line.split()
                    gene = parts[1]
                    valid_coef, test_coef, valid_slope, test_slope = parts[2], parts[3], parts[4], parts[5]
                    n = fold_test_n[ik_fold]
                    print(f"{variant},{ik_fold},{i_gene_min},{gene},{valid_coef},{test_coef},{valid_slope},{test_slope},{n}")
