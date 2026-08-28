"""Script-first language detection for the project's supported languages."""

from .detector import DetectionResult, LanguageScore, detect

__all__ = ["DetectionResult", "LanguageScore", "detect"]
