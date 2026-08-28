"""Script-first whole-text and mixed-span language detection."""

from .detector import (
    DetectionResult,
    DetectionSegment,
    LanguageScore,
    MixedDetectionResult,
    detect,
    detect_mixed,
)

__all__ = [
    "DetectionResult",
    "DetectionSegment",
    "LanguageScore",
    "MixedDetectionResult",
    "detect",
    "detect_mixed",
]
