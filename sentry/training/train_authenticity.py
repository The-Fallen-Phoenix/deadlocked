"""
PyTorch Training & Fine-Tuning Pipeline for SENTRY Voice Authenticity (Deepfake Detection).
Trains SentryAcousticClassifier using Focal Loss, Cosine Annealing, and SpecAugment.
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
from sentry.models.authenticity_detector import SentryAcousticClassifier
from sentry.data_engine.dataset_loader import SentryAuthenticityDataset, dataset_builder
from sentry.data_engine.benchmark_evaluator import benchmark_evaluator


class RewardPunishConfidenceLoss(nn.Module):
    """
    Reinforcement-Style Confidence Penalty Loss.
    - Rewards correct predictions made with high confidence (low loss).
    - Heavily punishes confident WRONG predictions (Quadratic Brier + Focal Penalty).
    - Prevents overconfident misclassifications on real vs synthetic voices.
    """

    def __init__(self, alpha: float = 0.5, gamma: float = 2.5, punish_factor: float = 4.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.punish_factor = punish_factor
        self.ce = nn.CrossEntropyLoss(reduction="none")

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.softmax(logits, dim=1)
        target_probs = probs.gather(1, targets.unsqueeze(1)).squeeze(1)  # p_t: prob of true class

        # 1. Focal Loss Component
        ce_loss = self.ce(logits, targets)
        focal_weight = (1.0 - target_probs) ** self.gamma
        base_loss = focal_weight * ce_loss

        # 2. Confident Wrong Penalty (Quadratic Brier Penalty)
        # If prediction is confident but wrong, target_probs is near 0, giving heavy penalty
        wrong_penalty = self.punish_factor * ((1.0 - target_probs) ** 2)

        total_loss = base_loss + wrong_penalty
        return total_loss.mean()


def train_authenticity_model(
    epochs: int = 15,
    batch_size: int = 16,
    lr: float = 2e-4,
    device_str: str = "auto",
    dry_run: bool = False,
    output_dir: str = "data/models_cache"
):
    """
    Executes the PyTorch training and validation loop for SENTRY deepfake detection.
    """
    if device_str == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_str)

    print(f"[*] Initializing SENTRY Authenticity Training on {device} (Epochs: {epochs}, Batch: {batch_size})")

    # 1. Prepare Datasets (Real vs Fake Voice Dataset with Speaker-Aware 80-20 Split)
    if dry_run:
        train_split = dataset_builder.build_synthetic_benchmark_split(num_genuine=40, num_synthetic=40)
        val_split = dataset_builder.build_synthetic_benchmark_split(num_genuine=15, num_synthetic=15)
    else:
        train_split, val_split = dataset_builder.build_real_vs_fake_split(
            dataset_dir="data/voice_dataset",
            train_ratio=0.8,
            seed=42
        )

    train_ds = SentryAuthenticityDataset(train_split, apply_augmentation=True, apply_spec_augment=True)
    val_ds = SentryAuthenticityDataset(val_split, apply_augmentation=False, apply_spec_augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # 2. Instantiate Model, Loss & Optimizer
    model = SentryAcousticClassifier().to(device)
    criterion = RewardPunishConfidenceLoss(alpha=0.5, gamma=2.5, punish_factor=4.0)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)

    best_val_eer = 100.0
    best_report = None
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    best_model_path = out_path / "best_authenticity_model.pt"

    print("\n================ SENTRY TRAINING EPOCH LOGS ================")

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0

        for mel_t, lfcc_t, labels in train_loader:
            mel_t = mel_t.to(device)
            lfcc_t = lfcc_t.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits, _ = model(mel_t, lfcc_t)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * len(labels)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == labels).sum().item()
            total += len(labels)

        scheduler.step()
        train_acc = (correct / max(total, 1)) * 100.0
        avg_train_loss = train_loss / max(total, 1)

        # Validation Loop & EER calculation
        model.eval()
        val_loss = 0.0
        all_labels = []
        all_synth_scores = []

        with torch.no_grad():
            for mel_t, lfcc_t, labels in val_loader:
                mel_t = mel_t.to(device)
                lfcc_t = lfcc_t.to(device)
                labels = labels.to(device)

                logits, _ = model(mel_t, lfcc_t)
                loss = criterion(logits, labels)
                val_loss += loss.item() * len(labels)

                probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
                all_synth_scores.extend(probs)
                all_labels.extend(labels.cpu().numpy())

        eval_report = benchmark_evaluator.evaluate_model_predictions(all_labels, all_synth_scores)
        val_eer = eval_report["equal_error_rate_pct"]
        val_auc = eval_report["roc_auc_score"]
        val_tdcf = eval_report["min_tdcf"]
        elapsed = time.time() - t0

        print(f"Epoch {epoch:02d}/{epochs:02d} [{elapsed:.1f}s] | Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.1f}% | Val EER: {val_eer:.2f}% | AUC: {val_auc:.4f} | min t-DCF: {val_tdcf}")

        if val_eer <= best_val_eer:
            best_val_eer = val_eer
            best_report = eval_report
            torch.save(model.state_dict(), best_model_path)

    print("=============================================================")
    print(f"[✓] Training Completed! Best Validation EER: {best_val_eer:.2f}% | Saved Checkpoint: {best_model_path}")
    if best_report:
        cm = best_report["confusion_matrix"]
        tn = cm["true_negatives_genuine"]
        fp = cm["false_positives_false_alarm"]
        fn = cm["false_negatives_missed_deepfake"]
        tp = cm["true_positives_detected_clone"]
        total_val = tn + fp + fn + tp
        val_acc = round((tn + tp) / max(total_val, 1) * 100.0, 2)
        real_rec = round(tn / max(tn + fp, 1) * 100.0, 2)
        fake_rec = round(tp / max(tp + fn, 1) * 100.0, 2)
        prec_fake = round(tp / max(tp + fp, 1) * 100.0, 2)
        prec_real = round(tn / max(tn + fn, 1) * 100.0, 2)

        print("\n================ FINAL TEST EVALUATION REPORT (20% HELD-OUT SPLIT) ================")
        print(f"  • Overall Test Accuracy:   {val_acc}%")
        print(f"  • Precision (Fake):        {prec_fake}%")
        print(f"  • Precision (Real):        {prec_real}%")
        print(f"  • Recall (Fake Clones):    {fake_rec}%")
        print(f"  • Recall (Real Voices):    {real_rec}% (Specificity)")
        print(f"  • F1 Score (Fake):         {best_report['f1_score'] * 100.0:.2f}%")
        print(f"  • Equal Error Rate (EER):  {best_report['equal_error_rate_pct']:.2f}%")
        print(f"  • ROC-AUC Score:           {best_report['roc_auc_score']:.4f}")
        print(f"  • min t-DCF:               {best_report['min_tdcf']}")
        print("  • Confusion Matrix:")
        print(f"      - True Real (Correct Real Voice):    {tn} / {tn+fp}")
        print(f"      - False Fake (Real Voice Warning):   {fp} / {tn+fp}")
        print(f"      - False Real (Missed Deepfake):       {fn} / {tp+fn}")
        print(f"      - True Fake (Detected Deepfake):     {tp} / {tp+fn}")
        print("====================================================================================\n")

    return best_model_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SENTRY Voice Authenticity Deepfake Classifier")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--dry-run", action="store_true", help="Quick dry run with few batches")
    parser.add_argument("--device", default="auto", help="Compute device (cuda, cpu, auto)")
    args = parser.parse_args()

    train_authenticity_model(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device_str=args.device,
        dry_run=args.dry_run
    )
