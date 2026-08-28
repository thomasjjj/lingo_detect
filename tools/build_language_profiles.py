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
    "ar-Arab-ACM": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample_acm.txt"),
    "ar-Arab-ACQ": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample_acq.txt"),
    "ar-Arab-AJP": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample_ajp.txt"),
    "ar-Arab-APC": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample_apc.txt"),
    "ar-Arab-ARS": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample_ars.txt"),
    "ar-Arab-ARZ": ("ar", "Arab", ROOT / "corpora" / "arabic" / "sample_arz.txt"),
    "az-Arab": ("az", "Arab", ROOT / "corpora" / "azerbaijani" / "sample_arab.txt"),
    "az-Cyrl": ("az", "Cyrl", ROOT / "corpora" / "azerbaijani" / "sample_cyrl.txt"),
    "az-Latn": ("az", "Latn", ROOT / "corpora" / "azerbaijani" / "sample.txt"),
    "en-Latn": ("en", "Latn", ROOT / "corpora" / "english" / "sample.txt"),
    "fa-Arab": ("fa", "Arab", ROOT / "corpora" / "persian" / "sample.txt"),
    "fa-Arab-Dari": ("fa", "Arab", ROOT / "corpora" / "persian" / "sample_dari.txt"),
    "he-Hebr": ("he", "Hebr", ROOT / "corpora" / "hebrew" / "sample.txt"),
    "hy-Armn": ("hy", "Armn", ROOT / "corpora" / "armenian" / "sample.txt"),
    "ka-Geor": ("ka", "Geor", ROOT / "corpora" / "georgian" / "sample.txt"),
    "kk-Cyrl": ("kk", "Cyrl", ROOT / "corpora" / "kazakh" / "sample.txt"),
    "ku-Arab": ("ku", "Arab", ROOT / "corpora" / "kurdish" / "sample.txt"),
    "ku-Latn": ("ku", "Latn", ROOT / "corpora" / "kurdish" / "sample_latn.txt"),
    "ky-Cyrl": ("ky", "Cyrl", ROOT / "corpora" / "kyrgyz" / "sample.txt"),
    "pa-Arab": ("pa", "Arab", ROOT / "corpora" / "punjabi" / "sample.txt"),
    "ps-Arab": ("ps", "Arab", ROOT / "corpora" / "pashto" / "sample.txt"),
    "ru-Cyrl": ("ru", "Cyrl", ROOT / "corpora" / "russian" / "sample.txt"),
    "tg-Cyrl": ("tg", "Cyrl", ROOT / "corpora" / "tajik" / "sample.txt"),
    "tk-Cyrl": ("tk", "Cyrl", ROOT / "corpora" / "turkmen" / "sample_cyrl.txt"),
    "tk-Latn": ("tk", "Latn", ROOT / "corpora" / "turkmen" / "sample.txt"),
    "tr-Latn": ("tr", "Latn", ROOT / "corpora" / "turkish" / "sample.txt"),
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
    "sd-Arab": ("sd", "Arab", ROOT / "corpora" / "sindhi" / "sample.txt"),
    "yi-Hebr": ("yi", "Hebr", ROOT / "corpora" / "yiddish" / "sample.txt"),
}


def ngrams(text: str) -> Counter[str]:
    normalised = (
        unicodedata.normalize("NFKC", text)
        .casefold()
        .replace("i\u0307", "i")
        .translate(APOSTROPHES)
    )
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
