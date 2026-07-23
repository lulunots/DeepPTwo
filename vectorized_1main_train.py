"""
Fast, properly-batched replacement for 1main_train.py.

Same reasoning as vectorized_model_AE.py: the original training_epoch()/
predict() in model_MLP.py loop one sample at a time (even under a nominal
batch_size), because MLP_regression.forward() does a mean-pool over the
tile dimension to handle slides with a variable number of tiles (ragged
data). In our per-cell setup every sample has exactly 1 tile, so that
mean-pool is a no-op and the per-sample loop is unnecessary overhead --
this script stacks same-shaped samples into real batches and lets
nn.Linear do genuine batched matrix ops instead.

REUSES UNCHANGED, for output-format compatibility:
  - model_MLP.MLP_regression (identical class -- saved state_dict loads
    fine with the original code)
  - utils.load_dataset(), utils.compute_coef_slope(), utils.analyze_result()
    (the final test-set evaluation/plotting/saving step still uses the
    original -- slower, but only run ONCE, not per epoch, so its cost is
    negligible)

Usage:
    python3 vectorized_1main_train.py <project> <ik_fold> <il_fold> <i_gene_min> <i_gene_step> [--batch-size 256]
"""

import os
import sys
import time
import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_MLP import MLP_regression, analyze_result
from utils import load_dataset, compute_coef_slope, init_random_seed

device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')


def stack_dataset(subset):
    """Pull every sample out of a Subset(SlideRNADataset) and stack into
    clean 2D tensors -- valid because every sample has exactly 1 tile."""
    xs, ys = [], []
    for i in range(len(subset)):
        x, y = subset[i]           # x: [1, 512], y: [n_genes]
        xs.append(x)
        ys.append(y)
    X = torch.cat(xs, dim=0)       # [n_samples, 512]  (squeezes the tile dim)
    Y = torch.stack(ys, dim=0)     # [n_samples, n_genes]
    return X, Y


def fast_epoch(model, optimizer, X, Y, batch_size, train, loss_fn):
    """One pass over X/Y in real batches. train=True updates weights."""
    n = X.shape[0]
    idx = torch.randperm(n) if train else torch.arange(n)

    model.train() if train else model.eval()

    losses = []
    all_preds, all_labels = [], []

    ctx = torch.enable_grad() if train else torch.no_grad()
    with ctx:
        for start in range(0, n, batch_size):
            batch_idx = idx[start:start + batch_size]
            xb = X[batch_idx].to(device)
            yb = Y[batch_idx].to(device)

            # bypass forward()'s mean-over-tiles -- each sample here is
            # already exactly 1 tile, so this is mathematically identical,
            # just batched properly across samples instead of looped
            pred = model.layer1(model.layer0(xb))

            loss = loss_fn(pred, yb)

            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            losses.append(loss.item())
            all_preds.append(pred.detach().cpu().numpy())
            all_labels.append(yb.detach().cpu().numpy())

    all_preds = np.concatenate(all_preds, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)
    coef, slope = compute_coef_slope(all_labels, all_preds)

    return np.mean(losses), np.mean(coef), np.mean(slope), all_labels, all_preds


def main():
    project = sys.argv[1]
    ik_fold = int(sys.argv[2])
    il_fold = int(sys.argv[3])
    i_gene_min = int(sys.argv[4])
    i_gene_step = int(sys.argv[5])
    batch_size = 32  # matches original -- not exposed as a CLI flag

    print("device:", device)
    init_random_seed(random_seed=42)

    rna_type = "pearson_zscored"
    print("rna_type:", rna_type)

    n_inputs = 512
    n_hiddens = 512
    dropout = 0.2
    learning_rate = 0.0001
    max_epochs, patience = 500, 50

    path2features = "../12AE/"
    path2target = "../10metadata/"
    path2split = "../10metadata/"

    gene_file = f"{path2target}{project}_genes.txt"
    genes = np.loadtxt(gene_file, dtype="str")
    i_gene_max = i_gene_min + i_gene_step
    genes = genes[i_gene_min:i_gene_max][:, 0]
    print("len(genes):", len(genes))

    result_dir = "results/%s/result_%s_%s_%s" % (project, ik_fold, il_fold, i_gene_min)
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    train_set, valid_set, test_set = load_dataset(
        path2features, path2target, path2split, rna_type,
        ik_fold, il_fold, genes, project
    )

    print("stacking train/valid sets into batched tensors...")
    X_train, Y_train = stack_dataset(train_set)
    X_valid, Y_valid = stack_dataset(valid_set)
    print(f"X_train: {X_train.shape}, X_valid: {X_valid.shape}")

    bias_init = torch.nn.Parameter(torch.Tensor(Y_train.numpy().mean(axis=0)).to(device))
    n_outputs = len(genes)

    model = MLP_regression(n_inputs, n_hiddens, n_outputs, dropout, bias_init)
    model.to(device)
    print(model)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.MSELoss()

    train_loss_list, train_coef_list, train_slope_list = [], [], []
    valid_loss_list, valid_coef_list, valid_slope_list = [], [], []

    start_time = time.time()
    epoch_since_best, valid_coef_old = 0, -1.0
    valid_labels, valid_preds = None, None

    for e in range(max_epochs):
        epoch_since_best += 1

        train_loss, train_coef, train_slope, _, _ = fast_epoch(
            model, optimizer, X_train, Y_train, batch_size, train=True, loss_fn=loss_fn
        )
        valid_loss, valid_coef, valid_slope, valid_labels, valid_preds = fast_epoch(
            model, optimizer, X_valid, Y_valid, batch_size, train=False, loss_fn=loss_fn
        )

        elapsed = time.time() - start_time
        print(f"epoch: {e}/{max_epochs}, time: {elapsed:.1f}s, "
              f"train_loss: {train_loss:.4f}, coef: {train_coef:.4f}, slope: {train_slope:.4f}, "
              f"valid_loss: {valid_loss:.4f}, coef: {valid_coef:.4f}, slope: {valid_slope:.4f}")

        train_loss_list.append(train_loss)
        train_coef_list.append(train_coef)
        train_slope_list.append(train_slope)
        valid_loss_list.append(valid_loss)
        valid_coef_list.append(valid_coef)
        valid_slope_list.append(valid_slope)

        if valid_coef > valid_coef_old:
            epoch_since_best = 0
            valid_coef_old = valid_coef

        if epoch_since_best == patience:
            print(f"Early stopping at epoch {e + 1}")
            break

    print(f"fit -- completed -- time: {time.time() - start_time:.2f}s")

    # hand off to the ORIGINAL, unmodified analyze_result() -- only runs
    # predict(model, test_set) ONCE here, using the slow-but-correct
    # per-sample loop; negligible cost for a single pass
    analyze_result(
        result_dir, genes, model,
        train_loss_list, train_coef_list, train_slope_list,
        valid_loss_list, valid_coef_list, valid_slope_list,
        valid_labels, valid_preds, test_set
    )

    print("--- completed ---")


if __name__ == "__main__":
    main()
