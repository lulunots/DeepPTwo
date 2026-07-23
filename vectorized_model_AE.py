"""
Fast, properly-batched replacement for 1main_AE.py.

The original script processes samples one at a time in a Python loop
(even under a nominal batch_size), because in general DeepPT usage
different slides have different numbers of tiles (ragged data). In our
case every "slide" (single-cell crop) has exactly 1 tile -- always the
same shape (1, 2048) -- so there's no raggedness to handle. This lets us
stack the whole dataset into one clean 2D tensor and do REAL batched
matrix operations (hundreds/thousands of samples per forward/backward
pass), instead of one sample at a time.

Output format matches the original AE step exactly, so 13DeepPT_train
scripts work unmodified:
  - {project}_features_AE.npy: list of (slide_name, y) tuples, y shape (1, 512)
  - {project}_model_AE.pth: trained encoder+decoder state dict

Usage:
    python3 fast_ae_training.py <project> [--batch-size 512] [--epochs 500]
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader, random_split


class AutoEncoder(nn.Module):
    """Identical architecture to model_AE.py's AutoEncoder, for state_dict compatibility."""
    def __init__(self, n_inputs, n_hiddens, n_outputs):
        super().__init__()
        self.encoder = nn.Sequential(nn.Linear(n_inputs, n_hiddens), nn.ReLU())
        self.decoder = nn.Sequential(nn.Linear(n_hiddens, n_outputs), nn.ReLU())

    def forward(self, x):
        return self.decoder(self.encoder(x))


def main(project, batch_size, max_epochs, lr, seed):
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print("device:", device)

    path2features = "../11slide_processing/"
    features_file = f"{path2features}{project}_features.npy"

    print(f"loading {features_file}")
    features = np.load(features_file, allow_pickle=True)
    n_samples = len(features)
    print(f"n_samples: {n_samples}")

    slide_names = [features[i][0] for i in range(n_samples)]

    ## stack all samples into one clean (n_samples, 2048) array -- valid
    ## because every sample here has exactly 1 tile (shape (1, 2048))
    tile_counts = [features[i][1].shape[0] for i in range(n_samples)]
    if not all(t == 1 for t in tile_counts):
        raise ValueError(
            f"Expected every sample to have exactly 1 tile, but found tile counts "
            f"ranging {min(tile_counts)}-{max(tile_counts)}. This fast script assumes "
            f"the one-crop-per-slide setup -- use the original 1main_AE.py if your "
            f"data has multiple tiles per slide."
        )

    X = np.concatenate([features[i][1] for i in range(n_samples)], axis=0)  ## (n_samples, 2048)
    print(f"X.shape: {X.shape}")

    n_inputs = X.shape[1]
    n_hiddens = 512
    n_outputs = n_inputs

    X_tensor = torch.from_numpy(X).float()
    dataset = TensorDataset(X_tensor)

    n_test = max(1, int(0.1 * n_samples))
    n_train = n_samples - n_test
    train_set, test_set = random_split(dataset, [n_train, n_test],
                                        generator=torch.Generator().manual_seed(seed))
    print(f"n_train: {n_train}, n_test: {n_test}")

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

    model = AutoEncoder(n_inputs, n_hiddens, n_outputs).to(device)
    print(model)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    train_loss_history = []
    test_loss_history = []

    import time
    start_time = time.time()

    for epoch in range(max_epochs):
        model.train()
        train_losses = []
        for (batch,) in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            pred = model(batch)
            loss = loss_fn(pred, batch)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        model.eval()
        test_losses = []
        with torch.no_grad():
            for (batch,) in test_loader:
                batch = batch.to(device)
                pred = model(batch)
                loss = loss_fn(pred, batch)
                test_losses.append(loss.item())

        train_loss = np.mean(train_losses)
        test_loss = np.mean(test_losses)
        train_loss_history.append(train_loss)
        test_loss_history.append(test_loss)

        elapsed = time.time() - start_time
        print(f"epoch: {epoch}/{max_epochs}, time: {elapsed:.1f}s, train_loss: {train_loss:.4f}, test_loss: {test_loss:.4f}")

    ## -----------------------------------------------------------------
    ## save model checkpoint (same filename convention as original)
    torch.save(model.state_dict(), f"{project}_model_AE.pth")
    np.savetxt("loss.txt", np.array((train_loss_history, test_loss_history)).T, fmt="%f")

    ## -----------------------------------------------------------------
    ## encode ALL samples (not just train/test split) in original order,
    ## producing the exact (slide_name, y) format 13DeepPT_train expects
    print("encoding all samples for output...")
    model.eval()
    features_AE = []
    with torch.no_grad():
        for batch_start in range(0, n_samples, batch_size):
            batch_end = min(batch_start + batch_size, n_samples)
            batch = X_tensor[batch_start:batch_end].to(device)
            y = model.encoder(batch).detach().cpu().numpy()  ## (batch, 512)

            for i in range(batch_end - batch_start):
                idx = batch_start + i
                features_AE.append((slide_names[idx], y[i:i+1]))  ## shape (1, 512) -- "1 tile"

    np.save(f"{project}_features_AE.npy", np.array(features_AE, dtype=object))
    print(f"saved {project}_features_AE.npy, len: {len(features_AE)}")
    print("--- completed ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fast, properly-batched AE training for one-tile-per-slide data")
    parser.add_argument("project", help="Project name (matches {project}_features.npy)")
    parser.add_argument("--batch-size", "-b", type=int, default=512, help="Batch size (default: 512)")
    parser.add_argument("--epochs", "-e", type=int, default=500, help="Number of epochs (default: 500, matches original)")
    parser.add_argument("--lr", type=float, default=0.0001, help="Learning rate (default: 0.0001, matches original)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    main(args.project, args.batch_size, args.epochs, args.lr, args.seed)
