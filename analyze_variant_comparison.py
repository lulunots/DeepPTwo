"""
Full comparison analysis from the consolidated coef CSV -- runs anywhere,
no pandas/scipy needed (pure standard library).

Usage:
    python analyze_variant_comparison.py all_coef_data.csv
"""

import sys
import csv
import math
from collections import defaultdict

if len(sys.argv) != 2:
    raise SystemExit(f"Usage: python {sys.argv[0]} <consolidated_csv_path>")

csv_path = sys.argv[1]

rows = []
with open(csv_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row["valid_coef"] = float(row["valid_coef"])
        row["test_coef"] = float(row["test_coef"])
        row["valid_slope"] = float(row["valid_slope"])
        row["test_slope"] = float(row["test_slope"])
        row["ik_fold"] = int(row["ik_fold"])
        row["i_gene_min"] = int(row["i_gene_min"])
        row["test_n"] = int(row["test_n"])
        rows.append(row)

print(f"Loaded {len(rows)} gene-fold entries")

def p_value_one_sided(r, n):
    if abs(r) >= 1:
        return 0.0
    t = r * math.sqrt((n - 2) / (1 - r**2))
    p_two_sided = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    return p_two_sided / 2 if r > 0 else 1 - p_two_sided / 2


def holm_sidak_correct(p_values):
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    for rank, (orig_idx, p) in enumerate(indexed):
        corrected[orig_idx] = 1 - (1 - p) ** (n - rank)
    return corrected


variants = sorted(set(r["variant"] for r in rows))

print("\n=== 1. Whole-panel comparison (test_coef, averaged per gene across folds) ===")
for variant in variants:
    per_gene = defaultdict(list)
    for r in rows:
        if r["variant"] == variant:
            per_gene[r["gene"]].append(r["test_coef"])

    avg_coefs = [sum(v) / len(v) for v in per_gene.values()]
    avg_coefs.sort(reverse=True)

    mean_c = sum(avg_coefs) / len(avg_coefs)
    median_c = avg_coefs[len(avg_coefs) // 2]
    n_above_01 = sum(1 for c in avg_coefs if c > 0.1)
    n_above_02 = sum(1 for c in avg_coefs if c > 0.2)

    print(f"\n{variant} (n_genes={len(avg_coefs)}):")
    print(f"  mean test_coef: {mean_c:.4f}")
    print(f"  median test_coef: {median_c:.4f}")
    print(f"  max test_coef: {avg_coefs[0]:.4f}")
    print(f"  genes with mean test_coef > 0.1: {n_above_01}")
    print(f"  genes with mean test_coef > 0.2: {n_above_02}")

print("\n\n=== 2. Significance (Holm-Sidak corrected, per gene-fold entry) ===")
for variant in variants:
    variant_rows = [r for r in rows if r["variant"] == variant]
    p_values = [p_value_one_sided(r["test_coef"], r["test_n"]) for r in variant_rows]
    p_adj = holm_sidak_correct(p_values)

    n_sig = sum(1 for p in p_adj if p < 0.05)
    n_sig_and_meaningful = sum(1 for p, r in zip(p_adj, variant_rows)
                               if p < 0.05 and abs(r["test_coef"]) > 0.1)

    print(f"\n{variant}:")
    print(f"  significant at padj<0.05: {n_sig} / {len(variant_rows)}")
    print(f"  significant AND |test_coef|>0.1: {n_sig_and_meaningful} / {len(variant_rows)}")

print("\n\n=== 3. Top-gene overlap: same genes, weaker signal? Or different genes? ===")
top_n = 20
top_genes_by_variant = {}
for variant in variants:
    per_gene = defaultdict(list)
    for r in rows:
        if r["variant"] == variant:
            per_gene[r["gene"]].append(r["test_coef"])
    avg = {g: sum(v) / len(v) for g, v in per_gene.items()}
    ranked = sorted(avg.items(), key=lambda x: -x[1])
    top_genes_by_variant[variant] = [g for g, c in ranked[:top_n]]

if len(variants) == 2:
    set_a = set(top_genes_by_variant[variants[0]])
    set_b = set(top_genes_by_variant[variants[1]])
    overlap = set_a & set_b
    print(f"\nTop {top_n} genes overlap between {variants[0]} and {variants[1]}: "
          f"{len(overlap)} / {top_n}")
    print(f"Shared top genes: {sorted(overlap)}")

print("\n\n=== 4. Validation vs test consistency (per variant) ===")
for variant in variants:
    variant_rows = [r for r in rows if r["variant"] == variant]
    diffs = [r["valid_coef"] - r["test_coef"] for r in variant_rows]
    mean_diff = sum(diffs) / len(diffs)

    valid_vals = [r["valid_coef"] for r in variant_rows]
    test_vals = [r["test_coef"] for r in variant_rows]
    n = len(valid_vals)
    mean_v = sum(valid_vals) / n
    mean_t = sum(test_vals) / n
    cov = sum((v - mean_v) * (t - mean_t) for v, t in zip(valid_vals, test_vals)) / n
    std_v = math.sqrt(sum((v - mean_v) ** 2 for v in valid_vals) / n)
    std_t = math.sqrt(sum((t - mean_t) ** 2 for t in test_vals) / n)
    corr = cov / (std_v * std_t) if std_v > 0 and std_t > 0 else float("nan")

    print(f"\n{variant}:")
    print(f"  mean(valid_coef - test_coef): {mean_diff:.4f}  (positive = valid overestimates test)")
    print(f"  correlation between valid_coef and test_coef across genes: {corr:.4f}")
