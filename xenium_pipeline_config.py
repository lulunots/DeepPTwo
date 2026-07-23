"""
Single source of truth for the two-slide fold assignment.

Import this in every script that needs to know which slide is
train/test for a given ik_fold — never re-derive the order from a dict's
insertion order or a dataframe's row order, since those can silently
diverge from each other.

ik_fold=0: train on SLIDE_ORDER[0], test on SLIDE_ORDER[1]
ik_fold=1: train on SLIDE_ORDER[1], test on SLIDE_ORDER[0]
"""

SLIDE_ORDER = ["4851A", "5626A"]
PROJECT = "AVD_61FEX"

# Per-slide filename naming is INCONSISTENT within the same variant:
#   5626A: {cell_id}{suffix}.npy                          e.g. 5626A_aaaa...-1_expanded_padded.npy
#   4851A: {slide}_b'{barcode}'{suffix}.npy                e.g. 4851A_b'aaaa...-1'_expanded_padded.npy
#          (a literal leftover Python bytes-repr baked into the filename
#          during 4851A's crop/rename step -- confirmed via directory listing,
#          not a guess)
# This was confirmed for "expanded_padded". For "padded", it's the same
# underlying crop/rename source per slide (just a different image transform
# downstream), so the same pattern is EXPECTED but should still be verified
# before trusting it -- don't assume twice in a row.
SLIDE_NAMING = {
    "4851A": "bytes_repr",
    "5626A": "plain",
}

DATASET_VARIANTS = {
    "expanded_padded": {
        "features_folder": "/working/lab_quann/louiseN/DeepPT/11slide_processing/expanded_padded_BC_benchmark_features/",
        "suffix": "_expanded_padded",
    },
    "padded": {
        "features_folder": "/working/lab_quann/louiseN/DeepPT/11slide_processing/padded_BC_benchmark_features",
        "suffix": "_padded",   # confirmed via repr() check
    },
}
