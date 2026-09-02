"""Generate the packaged character n-gram profiles from exploration corpora."""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "lingo_detect" / "profiles.json"
PROFILE_SIZE = 800
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
    "bn-Beng": ("bn", "Beng", ROOT / "corpora" / "bengali" / "sample.txt"),
    "de-Latn": ("de", "Latn", ROOT / "corpora" / "german" / "sample.txt"),
    "en-Latn": ("en", "Latn", ROOT / "corpora" / "english" / "sample.txt"),
    "es-Latn": ("es", "Latn", ROOT / "corpora" / "spanish" / "sample.txt"),
    "fa-Arab": ("fa", "Arab", ROOT / "corpora" / "persian" / "sample.txt"),
    "fa-Arab-Dari": ("fa", "Arab", ROOT / "corpora" / "persian" / "sample_dari.txt"),
    "fr-Latn": ("fr", "Latn", ROOT / "corpora" / "french" / "sample.txt"),
    "ha-Latn": ("ha", "Latn", ROOT / "corpora" / "hausa" / "sample.txt"),
    "he-Hebr": ("he", "Hebr", ROOT / "corpora" / "hebrew" / "sample.txt"),
    "hi-Deva": ("hi", "Deva", ROOT / "corpora" / "hindi" / "sample.txt"),
    "hy-Armn": ("hy", "Armn", ROOT / "corpora" / "armenian" / "sample.txt"),
    "id-Latn": ("id", "Latn", ROOT / "corpora" / "indonesian" / "sample.txt"),
    "ja-Jpan": ("ja", "Jpan", ROOT / "corpora" / "japanese" / "sample.txt"),
    "ka-Geor": ("ka", "Geor", ROOT / "corpora" / "georgian" / "sample.txt"),
    "kk-Cyrl": ("kk", "Cyrl", ROOT / "corpora" / "kazakh" / "sample.txt"),
    "ku-Arab": ("ku", "Arab", ROOT / "corpora" / "kurdish" / "sample.txt"),
    "ku-Latn": ("ku", "Latn", ROOT / "corpora" / "kurdish" / "sample_latn.txt"),
    "ky-Cyrl": ("ky", "Cyrl", ROOT / "corpora" / "kyrgyz" / "sample.txt"),
    "mr-Deva": ("mr", "Deva", ROOT / "corpora" / "marathi" / "sample.txt"),
    "pa-Arab": ("pa", "Arab", ROOT / "corpora" / "punjabi" / "sample.txt"),
    "pcm-Latn": (
        "pcm",
        "Latn",
        ROOT / "corpora" / "nigerian_pidgin" / "sample.txt",
    ),
    "pt-Latn": ("pt", "Latn", ROOT / "corpora" / "portuguese" / "sample.txt"),
    "ps-Arab": ("ps", "Arab", ROOT / "corpora" / "pashto" / "sample.txt"),
    "ru-Cyrl": ("ru", "Cyrl", ROOT / "corpora" / "russian" / "sample.txt"),
    "sw-Latn": ("sw", "Latn", ROOT / "corpora" / "swahili" / "sample.txt"),
    "te-Telu": ("te", "Telu", ROOT / "corpora" / "telugu" / "sample.txt"),
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
    "vi-Latn": ("vi", "Latn", ROOT / "corpora" / "vietnamese" / "sample.txt"),
    "sd-Arab": ("sd", "Arab", ROOT / "corpora" / "sindhi" / "sample.txt"),
    "yi-Hebr": ("yi", "Hebr", ROOT / "corpora" / "yiddish" / "sample.txt"),
    "zh-Hani": ("zh", "Hani", ROOT / "corpora" / "chinese" / "sample.txt"),
}


def tokens(text: str) -> list[str]:
    translated = text.translate(APOSTROPHES)
    result: list[str] = []
    current: list[str] = []
    for index, character in enumerate(translated):
        is_letter_or_mark = character.isalpha() or unicodedata.category(
            character
        ).startswith("M")
        apostrophe_inside_word = (
            character == "'"
            and bool(current)
            and index + 1 < len(translated)
            and (
                translated[index + 1].isalpha()
                or unicodedata.category(translated[index + 1]).startswith("M")
            )
        )
        if is_letter_or_mark or apostrophe_inside_word:
            current.append(character)
        elif current:
            result.append("".join(current))
            current = []
    if current:
        result.append("".join(current))
    return result


def ngrams(text: str) -> Counter[str]:
    normalised = (
        unicodedata.normalize("NFKC", text)
        .casefold()
        .replace("i\u0307", "i")
    )
    words = tokens(normalised)
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
