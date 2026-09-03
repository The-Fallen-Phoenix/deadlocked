"""
Biometric Speaker Verification and Voiceprint Embedding Engine for SENTRY.
Extracts 256-dimensional L2-normalized speaker voiceprint vectors and performs
cosine distance verification against enrolled identities.
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from sentry.core.config import settings
from sentry.audio.preprocessor import audio_preprocessor
from sentry.audio.features import feature_extractor


class SentrySpeakerEmbeddingNet(nn.Module):
    """
    Speaker Biometric Embedding Network (TDNN / ResNet architecture).
    Maps Mel-frequency representations to a 256-dimensional unit hypersphere.
    """

    def __init__(self, in_features: int = 80, embedding_dim: int = 256):
        super().__init__()
        self.conv1 = nn.Conv1d(in_features, 128, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(128)
        self.conv2 = nn.Conv1d(128, 128, kernel_size=3, dilation=2, padding=2)
        self.bn2 = nn.BatchNorm1d(128)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=3, dilation=3, padding=3)
        self.bn3 = nn.BatchNorm1d(256)

        # Statistical Pooling (Mean + Std Dev over time)
        # 256 * 2 = 512
        self.fc1 = nn.Linear(512, 384)
        self.bn4 = nn.BatchNorm1d(384)
        self.fc2 = nn.Linear(384, embedding_dim)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.Conv1d, nn.Linear)):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, 80, Time]
        h = F.relu(self.bn1(self.conv1(x)), inplace=True)
        h = F.relu(self.bn2(self.conv2(h)), inplace=True)
        h = F.relu(self.bn3(self.conv3(h)), inplace=True)

        # Temporal Statistical Pooling
        mean = torch.mean(h, dim=2)
        std = torch.std(h, dim=2) + 1e-6
        stats = torch.cat([mean, std], dim=1)  # [B, 512]

        e = F.relu(self.bn4(self.fc1(stats)), inplace=True)
        embedding = self.fc2(e)  # [B, 256]

        # L2-normalize to unit hypersphere
        normalized = F.normalize(embedding, p=2, dim=1)
        return normalized


class SpeakerVerifier:
    """
    High-level Biometric Speaker Verification Engine for SENTRY.
    Extracts speaker embeddings and evaluates claimed identity match.
    """

    def __init__(self, checkpoint_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentrySpeakerEmbeddingNet().to(self.device)

        from pathlib import Path
        candidates = [
            Path(checkpoint_path) if checkpoint_path else None,
            settings.data_dir / "models_cache" / "best_speaker_embedding_net.pt",
            Path("data/models_cache/best_speaker_embedding_net.pt")
        ]
        for ckpt in candidates:
            if ckpt and ckpt.exists():
                try:
                    state_dict = torch.load(str(ckpt), map_location=self.device)
                    self.model.load_state_dict(state_dict)
                    print(f"[*] SpeakerVerifier loaded model checkpoint from {ckpt}")
                    break
                except Exception as e:
                    print(f"[!] Warning: Failed loading speaker checkpoint {ckpt}: {e}")

        self.model.eval()
        self.match_threshold = settings.biometrics.match_threshold

    def extract_embedding(self, audio: np.ndarray) -> np.ndarray:
        """
        Extracts 256-dimensional unit speaker embedding from audio array.
        """
        if len(audio) < 1600:
            # Return zero vector if audio is too short
            return np.zeros(settings.biometrics.embedding_dim, dtype=np.float32)

        audio_tensor = audio_preprocessor.to_torch_tensor(audio).to(self.device)
        mel_spec = feature_extractor.extract_mel_spectrogram(audio_tensor)
        # Mel shape: [80, Time] -> [1, 80, Time]
        mel_t = torch.from_numpy(mel_spec).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            embedding = self.model(mel_t)
            emb_np = embedding.cpu().numpy()[0]

        return emb_np

    def compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculates Cosine Similarity between two voiceprint embeddings.
        Returns value in [-1.0, 1.0], typically mapped to [0.0, 1.0].
        """
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0
        dot = np.dot(emb1, emb2)
        cos_sim = float(dot / (norm1 * norm2))
        return float(np.clip(cos_sim, -1.0, 1.0))

    def verify_against_reference(
        self,
        audio: np.ndarray,
        reference_embedding: np.ndarray,
        claimed_speaker_name: Optional[str] = "Enrolled Profile"
    ) -> Dict[str, Any]:
        """
        Compares input audio against an enrolled reference voiceprint.
        """
        current_emb = self.extract_embedding(audio)
        similarity = self.compute_similarity(current_emb, reference_embedding)

        # Scale cosine similarity (-1.0 to 1.0) to percentage match (0.0 to 100.0%)
        # For normalized deep embeddings, similarity > 0.72 indicates strong speaker match
        match_confidence = float(np.clip((similarity + 0.2) / 1.2 * 100.0, 0.0, 100.0))

        if similarity >= self.match_threshold:
            status = "MATCH_CONFIRMED"
            is_match = True
            risk_contribution = 0.0
            description = f"Biometric voiceprint matches claimed identity ({claimed_speaker_name})."
        elif similarity >= self.match_threshold - settings.biometrics.ambiguous_margin:
            status = "AMBIGUOUS_MATCH"
            is_match = False
            risk_contribution = 0.45
            description = f"Ambiguous voiceprint match for {claimed_speaker_name}. Step-up verification recommended."
        else:
            status = "SPEAKER_MISMATCH"
            is_match = False
            risk_contribution = 0.90
            description = f"CRITICAL: Biometric voiceprint DOES NOT match claimed identity ({claimed_speaker_name})!"

        return {
            "claimed_speaker": claimed_speaker_name,
            "cosine_similarity": round(similarity, 4),
            "match_confidence_pct": round(match_confidence, 1),
            "is_match": is_match,
            "verification_status": status,
            "description": description,
            "speaker_mismatch_risk": round(risk_contribution, 3),
            "embedding_norm": round(float(np.linalg.norm(current_emb)), 3)
        }


speaker_verifier = SpeakerVerifier()
