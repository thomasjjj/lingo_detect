"""Generate the packaged character n-gram profiles from exploration corpora."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "lingo_detect" / "profiles.json"
PROFILE_SIZE = 800
WORD_PATTERN = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)
APOSTROPHES = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'"})

SOURCES = {
    "ar-Arab": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample.txt"),
    "en-Latn": ("en", "Latn", ROOT / "corpora" / "english" / "sample.txt"),
    "ps-Arab": ("ps", "Arab", ROOT / "corpora" / "pashto" / "sample.txt"),
    "ru-Cyrl": ("ru", "Cyrl", ROOT / "corpora" / "russian" / "sample.txt"),
    "tg-Cyrl": ("tg", "Cyrl", ROOT / "corpora" / "tajik" / "sample.txt"),
    "uk-Cyrl": ("uk", "Cyrl", ROOT / "corpora" / "ukrainian" / "sample.txt"),
    "ur-Arab": ("ur", "Arab", ROOT / "corpora" / "urdu" / "sample.txt"),
    "ug-Arab": ("ug", "Arab", ROOT / "corpora" / "uyghur" / "sample.txt"),
    "ug-Latn": ("ug", "Latn", ROOT / "corpora" / "uyghur" / "sample_latn.txt"),
    "ug-Cyrl": ("ug", "Cyrl", ROOT / "corpora" / "uyghur" / "sample_cyrl.txt"),
    "ug-Latn-UYY": (
        "ug",
        "Latn",
        ROOT / "corpora" / "uyghur" / "sample_yengi.txt",
    ),
    "uz-Latn": ("uz", "Latn", ROOT / "corpora" / "uzbek" / "sample.txt"),
    "uz-Cyrl": ("uz", "Cyrl", ROOT / "corpora" / "uzbek" / "sample_cyrl.txt"),
}


def ngrams(text: str) -> Counter[str]:
    normalised = unicodedata.normalize("NFKC", text).casefold().translate(APOSTROPHES)
    words = WORD_PATTERN.findall(normalised)
    counts: Counter[str] = Counter()
    for word in words:
        padded = f"^{word}$"
        for size in (2, 3, 4):
            counts.update(
                padded[index : index + size]
                for index in range(len(padded) - size + 1)
            )
    return counts


def main() -> None:
    profiles = {}
    for key, (language_code, script, source_path) in SOURCES.items():
        counts = ngrams(source_path.read_text(encoding="utf-8"))
        profiles[key] = {
            "language_code": language_code,
            "script": script,
            "ngrams": [item for item, _ in counts.most_common(PROFILE_SIZE)],
        }
        print(f"{key}: {len(profiles[key]['ngrams'])} n-grams")
    OUTPUT.write_text(
        json.dumps({"version": 1, "profiles": profiles}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
