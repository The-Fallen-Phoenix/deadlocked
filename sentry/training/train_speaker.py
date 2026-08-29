"""
PyTorch Training Pipeline for SENTRY Biometric Speaker Embedding Network.
Trains SentrySpeakerEmbeddingNet using Triplet Margin Loss for optimal identity separation.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import argparse
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from sentry.core.config import settings
from sentry.models.speaker_verifier import SentrySpeakerEmbeddingNet
from sentry.data_engine.dataset_loader import SentrySpeakerTripletDataset
from sentry.audio.synth_generator import scenario_generator


def train_speaker_model(
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 2e-4,
    margin: float = 0.3,
    device_str: str = "auto",
    dry_run: bool = False,
    output_dir: str = "data/models_cache"
):
    """
    Executes Triplet Loss metric learning for speaker voiceprint embeddings.
    """
    if device_str == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_str)

    print(f"[*] Initializing SENTRY Speaker Biometrics Training on {device} (Margin: {margin})")

    # 1. Synthesize multi-speaker reference pool
    num_speakers = 6 if dry_run else 16
    samples_per_spk = 3 if dry_run else 6
    speakers_dict = {}

    for s_idx in range(num_speakers):
        spk_id = f"spk_train_{s_idx}"
        base_f0 = 90.0 + s_idx * 10.0
        speakers_dict[spk_id] = [
            scenario_generator.generate_formant_speech(duration_sec=2.5, base_f0=base_f0 + np.random.uniform(-3, 3))
            for _ in range(samples_per_spk)
        ]

    train_ds = SentrySpeakerTripletDataset(speakers_dict, samples_per_epoch=40 if dry_run else 200)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    # 2. Model & Triplet Loss
    model = SentrySpeakerEmbeddingNet().to(device)
    criterion = nn.TripletMarginLoss(margin=margin, p=2)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    best_model_path = out_path / "best_speaker_embedding_net.pt"

    print("\n================ SENTRY SPEAKER BIOMETRICS EPOCH LOGS ================")

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        total_loss = 0.0

        for a_mel, p_mel, n_mel in train_loader:
            a_mel = a_mel.to(device)
            p_mel = p_mel.to(device)
            n_mel = n_mel.to(device)

            optimizer.zero_grad()
            emb_a = model(a_mel)
            emb_p = model(p_mel)
            emb_n = model(n_mel)

            loss = criterion(emb_a, emb_p, emb_n)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(a_mel)

        avg_loss = total_loss / len(train_ds)
        elapsed = time.time() - t0
        print(f"Epoch {epoch:02d}/{epochs:02d} [{elapsed:.1f}s] | Triplet Loss: {avg_loss:.4f}")

    torch.save(model.state_dict(), best_model_path)
    print("======================================================================")
    print(f"[✓] Speaker Biometrics Training Completed! Saved Checkpoint: {best_model_path}\n")
    return best_model_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SENTRY Speaker Biometric Verification Network")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--margin", type=float, default=0.3, help="Triplet margin")
    parser.add_argument("--dry-run", action="store_true", help="Quick dry run with few batches")
    args = parser.parse_args()

    train_speaker_model(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        margin=args.margin,
        dry_run=args.dry_run
    )
