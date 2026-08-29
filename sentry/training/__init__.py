"""
Training package for SENTRY platform.
"""
from sentry.training.train_authenticity import train_authenticity_model
from sentry.training.train_speaker import train_speaker_model

__all__ = ["train_authenticity_model", "train_speaker_model"]
