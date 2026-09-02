"""Build deterministic held-out cases from pinned multilingual corpora."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import random
import re
import tarfile
import tempfile
import unicodedata
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

try:
    from .uyghur_transliteration import (
        arabic_to_cyrillic,
        arabic_to_latin,
        arabic_to_new_script,
    )
except ImportError:  # Support ``python tools/build_test_samples.py``.
    from uyghur_transliteration import (
        arabic_to_cyrillic,
        arabic_to_latin,
        arabic_to_new_script,
    )


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "data" / "flores200_devtest.jsonl"
ARCHIVE_URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
ARCHIVE_SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"
RANDOM_SEED = 20260828
TARGET_LENGTHS = (1, 2, 3, 5, 10, 20, 50, 100)
CASES_PER_LENGTH = 5
USER_AGENT = "lingo-detect-test-builder/0.1 (educational language research)"
UDHR_COMMIT = "d3d38276c91668df9ac4e33e5dac7cd3a14c12b2"
UDHR_RAW_ROOT = (
    "https://raw.githubusercontent.com/wooorm/udhr/"
    f"{UDHR_COMMIT}/declaration"
)
NORTHERN_PASHTO_URL = (
    f"{UDHR_RAW_ROOT}/pbu.html"
)
REGIONAL_UDHR_SOURCES = (
    {
        "case_prefix": "az-cyrl",
        "expected_language": "az",
        "language_name": "Azerbaijani",
        "script": "Cyrl",
        "variety": "North",
        "source_code": "azj_cyrl",
        "source_url": f"{UDHR_RAW_ROOT}/azj_cyrl.html",
        "cases_per_length": 2,
    },
    {
        "case_prefix": "ku-kmr",
        "expected_language": "ku",
        "language_name": "Kurdish",
        "script": "Latn",
        "variety": "Northern (Kurmanji)",
        "source_code": "kmr",
        "source_url": f"{UDHR_RAW_ROOT}/kmr.html",
        "cases_per_length": 3,
    },
    {
        "case_prefix": "pa-pnb",
        "expected_language": "pa",
        "language_name": "Punjabi",
        "script": "Arab",
        "variety": "Western",
        "source_code": "pnb",
        "source_url": f"{UDHR_RAW_ROOT}/pnb.html",
        "cases_per_length": 5,
    },
    {
        "case_prefix": "tk-cyrl",
        "expected_language": "tk",
        "language_name": "Turkmen",
        "script": "Cyrl",
        "variety": None,
        "source_code": "tuk_cyrl",
        "source_url": f"{UDHR_RAW_ROOT}/tuk_cyrl.html",
        "cases_per_length": 1,
    },
)
TATOEBA_UZBEK_URL = (
    "https://downloads.tatoeba.org/exports/per_language/uzb/uzb_sentences.tsv.bz2"
)
TATOEBA_UZBEK_SHA256 = (
    "08c5d375d6cd9bef2b1610ccf1ad9d39e3559c4c2536c5adfd60253d5292e048"
)
NAIJA_NSC_COMMIT = "e1208ebb7111cf1180964d5a0012b6b273752324"
NAIJA_NSC_RAW_ROOT = (
    "https://raw.githubusercontent.com/UniversalDependencies/UD_Naija-NSC/"
    f"{NAIJA_NSC_COMMIT}"
)
NAIJA_NSC_TRAIN_URL = f"{NAIJA_NSC_RAW_ROOT}/pcm_nsc-ud-train.conllu"
NAIJA_NSC_TEST_URL = f"{NAIJA_NSC_RAW_ROOT}/pcm_nsc-ud-test.conllu"
NAIJA_NSC_TRAIN_SHA256 = (
    "2ecbbbd970575573da99c82897a08ce8c32ddc4f88d65bdc213e30e772ee4804"
)
NAIJA_NSC_TEST_SHA256 = (
    "59bb428a3435ed09f4e9cf9738d47875ba89f16f7fcd4f48d33b264c3e74bad9"
)

LANGUAGES = {
    "ar": {
        "name": "Arabic",
        "flores": "arb_Arab",
        "script": "Arab",
        "variety": "Modern Standard",
    },
    "ar-acm": {
        "code": "ar", "name": "Arabic", "flores": "acm_Arab",
        "script": "Arab", "variety": "Mesopotamian",
    },
    "ar-acq": {
        "code": "ar", "name": "Arabic", "flores": "acq_Arab",
        "script": "Arab", "variety": "Ta’izzi-Adeni",
    },
    "ar-ajp": {
        "code": "ar", "name": "Arabic", "flores": "ajp_Arab",
        "script": "Arab", "variety": "South Levantine",
    },
    "ar-apc": {
        "code": "ar", "name": "Arabic", "flores": "apc_Arab",
        "script": "Arab", "variety": "North Levantine",
    },
    "ar-ars": {
        "code": "ar", "name": "Arabic", "flores": "ars_Arab",
        "script": "Arab", "variety": "Najdi",
    },
    "ar-arz": {
        "code": "ar", "name": "Arabic", "flores": "arz_Arab",
        "script": "Arab", "variety": "Egyptian",
    },
    "az-latn": {
        "code": "az", "name": "Azerbaijani", "flores": "azj_Latn",
        "script": "Latn", "variety": "North",
    },
    "az-arab": {
        "code": "az", "name": "Azerbaijani", "flores": "azb_Arab",
        "script": "Arab", "variety": "South",
    },
    "bn": {
        "name": "Bengali", "flores": "ben_Beng", "script": "Beng",
        "minimum_script_share": 0.70,
    },
    "de": {"name": "German", "flores": "deu_Latn", "script": "Latn"},
    "en": {"name": "English", "flores": "eng_Latn", "script": "Latn"},
    "es": {"name": "Spanish", "flores": "spa_Latn", "script": "Latn"},
    "fa": {
        "name": "Persian (Farsi)",
        "flores": "pes_Arab",
        "script": "Arab",
        "variety": "Western",
    },
    "fa-dari": {
        "code": "fa",
        "name": "Persian",
        "flores": "prs_Arab",
        "script": "Arab",
        "variety": "Dari",
    },
    "fr": {"name": "French", "flores": "fra_Latn", "script": "Latn"},
    "ha": {"name": "Hausa", "flores": "hau_Latn", "script": "Latn"},
    "he": {"name": "Hebrew", "flores": "heb_Hebr", "script": "Hebr"},
    "hi": {
        "name": "Hindi", "flores": "hin_Deva", "script": "Deva",
        "minimum_script_share": 0.70,
    },
    "hy": {"name": "Armenian", "flores": "hye_Armn", "script": "Armn"},
    "id": {"name": "Indonesian", "flores": "ind_Latn", "script": "Latn"},
    "ja": {
        "name": "Japanese", "flores": "jpn_Jpan", "script": "Jpan",
        "minimum_script_share": 0.70,
    },
    "ka": {"name": "Georgian", "flores": "kat_Geor", "script": "Geor"},
    "kk": {"name": "Kazakh", "flores": "kaz_Cyrl", "script": "Cyrl"},
    "ku": {
        "name": "Kurdish", "flores": "ckb_Arab", "script": "Arab",
        "variety": "Central (Sorani)",
    },
    "ky": {"name": "Kyrgyz", "flores": "kir_Cyrl", "script": "Cyrl"},
    "mr": {
        "name": "Marathi", "flores": "mar_Deva", "script": "Deva",
        "minimum_script_share": 0.70,
    },
    "ps": {
        "name": "Pashto",
        "flores": "pbt_Arab",
        "script": "Arab",
        "variety": "Southern",
    },
    "pt": {"name": "Portuguese", "flores": "por_Latn", "script": "Latn"},
    "ru": {"name": "Russian", "flores": "rus_Cyrl", "script": "Cyrl"},
    "sd": {
        "name": "Sindhi",
        "flores": "snd_Arab",
        "script": "Arab",
        "filter_nonlexical_tokens": True,
    },
    "sw": {"name": "Swahili", "flores": "swh_Latn", "script": "Latn"},
    "te": {
        "name": "Telugu", "flores": "tel_Telu", "script": "Telu",
        "minimum_script_share": 0.70,
    },
    "tg": {"name": "Tajik", "flores": "tgk_Cyrl", "script": "Cyrl"},
    "tk": {"name": "Turkmen", "flores": "tuk_Latn", "script": "Latn"},
    "tr": {"name": "Turkish", "flores": "tur_Latn", "script": "Latn"},
    "uk": {"name": "Ukrainian", "flores": "ukr_Cyrl", "script": "Cyrl"},
    "ur": {"name": "Urdu", "flores": "urd_Arab", "script": "Arab"},
    "ug": {
        "name": "Uyghur",
        "flores": "uig_Arab",
        "script": "Arab",
        "alphabet": "Uyghur Arabic (UEY)",
    },
    "uz": {
        "name": "Uzbek",
        "flores": "uzn_Latn",
        "script": "Latn",
        "variety": "Northern",
    },
    "vi": {"name": "Vietnamese", "flores": "vie_Latn", "script": "Latn"},
    "yi": {
        "name": "Yiddish", "flores": "ydd_Hebr", "script": "Hebr",
        "variety": "Eastern",
    },
    "zh": {
        "name": "Mandarin Chinese",
        "flores": "zho_Hans",
        "script": "Hani",
        "variety": "Simplified",
        "filter_nonlexical_tokens": True,
        "minimum_script_share": 0.70,
    },
}


class ParagraphExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_paragraph = False
        self.parts: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "p":
            self.in_paragraph = True
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.in_paragraph:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self.in_paragraph:
            text = re.sub(r"\s+", " ", "".join(self.parts)).strip()
            if text:
                self.paragraphs.append(text)
            self.in_paragraph = False
            self.parts = []


def download_archive(destination: Path) -> None:
    request = urllib.request.Request(ARCHIVE_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def download_text(url: str) -> str:
    return download_bytes(url).decode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_language_lines(
    archive: tarfile.TarFile, flores_code: str, split: str = "devtest"
) -> list[str]:
    member_name = f"./flores200_dataset/{split}/{flores_code}.{split}"
    member = archive.getmember(member_name)
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"could not read {member_name}")
    return [
        unicodedata.normalize("NFC", line.strip())
        for line in source.read().decode("utf-8").splitlines()
        if line.strip()
    ]


def declared_script_share(text: str, script: str) -> float:
    names = [
        unicodedata.name(character, "")
        for character in text
        if character.isalpha()
    ]
    if not names:
        return 0.0
    if script == "Jpan":
        matching = sum(
            "HIRAGANA" in name
            or "KATAKANA" in name
            or "CJK UNIFIED IDEOGRAPH" in name
            or "CJK COMPATIBILITY IDEOGRAPH" in name
            for name in names
        )
    else:
        unicode_name = {
            "Beng": "BENGALI",
            "Deva": "DEVANAGARI",
            "Hani": "CJK",
            "Telu": "TELUGU",
        }[script]
        matching = sum(unicode_name in name for name in names)
    return matching / len(names)


def choose_window(
    lines: list[str],
    word_count: int,
    rng: random.Random,
    used_starts: set[int],
    used_texts: set[str],
    expected_script: str | None = None,
    minimum_script_share: float = 0.0,
) -> tuple[str, int, int]:
    for _ in range(10_000):
        line_index = rng.randrange(len(lines))
        if line_index in used_starts:
            continue
        first_line_words = lines[line_index].split()
        offset = rng.randrange(len(first_line_words))
        words = first_line_words[offset:]
        final_line_index = line_index
        while len(words) < word_count and final_line_index + 1 < len(lines):
            final_line_index += 1
            words.extend(lines[final_line_index].split())
        if len(words) < word_count:
            continue
        selected = words[:word_count]
        # Do not accidentally create punctuation-only or number-only "word"
        # cases. Punctuation attached to lexical tokens is retained.
        if not all(any(character.isalpha() for character in word) for word in selected):
            continue
        text = " ".join(selected)
        if text in used_texts:
            continue
        if (
            expected_script
            and declared_script_share(text, expected_script) < minimum_script_share
        ):
            continue
        used_starts.add(line_index)
        used_texts.add(text)
        return text, line_index + 1, final_line_index + 1
    raise RuntimeError(f"could not select a unique {word_count}-word window")


def read_naija_texts(data: bytes) -> list[str]:
    """Read normalized Nigerian Pidgin sentences from a pinned CoNLL-U file."""
    actual_hash = hashlib.sha256(data).hexdigest()
    known_hashes = {NAIJA_NSC_TRAIN_SHA256, NAIJA_NSC_TEST_SHA256}
    if actual_hash not in known_hashes:
        raise ValueError(f"NaijaSynCor SHA-256 mismatch: {actual_hash}")
    prefix = "# text_ortho = "
    return [
        unicodedata.normalize("NFC", line.removeprefix(prefix).strip())
        for line in data.decode("utf-8").splitlines()
        if line.startswith(prefix) and line.removeprefix(prefix).strip()
    ]


def build_nigerian_pidgin_cases(data: bytes) -> list[dict]:
    texts = read_naija_texts(data)
    used_starts: set[int] = set()
    used_texts: set[str] = set()
    cases = []
    for word_count in TARGET_LENGTHS:
        rng = random.Random(f"{RANDOM_SEED}:pcm_NSC:test:{word_count}")
        for case_number in range(1, CASES_PER_LENGTH + 1):
            text, sentence_start, sentence_end = choose_window(
                texts, word_count, rng, used_starts, used_texts
            )
            cases.append(
                {
                    "id": f"pcm-{word_count:03}w-{case_number:02}",
                    "expected_language": "pcm",
                    "language_name": "Nigerian Pidgin",
                    "script": "Latn",
                    "word_count": word_count,
                    "text": text,
                    "source": {
                        "dataset": "NaijaSynCor",
                        "split": "test",
                        "source_url": NAIJA_NSC_TEST_URL,
                        "source_commit": NAIJA_NSC_COMMIT,
                        "sentence_start": sentence_start,
                        "sentence_end": sentence_end,
                    },
                }
            )
    return cases


def build_cases(archive_path: Path) -> list[dict]:
    cases = []
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for case_prefix, language in LANGUAGES.items():
            language_code = language.get("code", case_prefix)
            lines = read_language_lines(archive, language["flores"])
            if language.get("filter_nonlexical_tokens"):
                lines = [
                    " ".join(
                        word
                        for word in line.split()
                        if any(character.isalpha() for character in word)
                    )
                    for line in lines
                ]
            used_starts: set[int] = set()
            used_texts: set[str] = set()
            for word_count in TARGET_LENGTHS:
                rng = random.Random(
                    f"{RANDOM_SEED}:{language['flores']}:{word_count}"
                )
                for case_number in range(1, CASES_PER_LENGTH + 1):
                    text, sentence_start, sentence_end = choose_window(
                        lines,
                        word_count,
                        rng,
                        used_starts,
                        used_texts,
                        language["script"] if language.get("minimum_script_share") else None,
                        language.get("minimum_script_share", 0.0),
                    )
                    cases.append(
                        {
                            "id": f"{case_prefix}-{word_count:03}w-{case_number:02}",
                            "expected_language": language_code,
                            "language_name": language["name"],
                            "script": language["script"],
                            "alphabet": language.get("alphabet"),
                            "variety": language.get("variety"),
                            "word_count": word_count,
                            "text": text,
                            "source": {
                                "dataset": "FLORES-200",
                                "split": "devtest",
                                "flores_code": language["flores"],
                                "sentence_start": sentence_start,
                                "sentence_end": sentence_end,
                            },
                        }
                    )
    return cases


def build_transliterated_uighur_cases(cases: list[dict]) -> list[dict]:
    """Create parallel held-out cases for three additional Uyghur alphabets."""
    variants = {
        "latn": ("Latn", "Uyghur Latin (ULY)", arabic_to_latin),
        "cyrl": ("Cyrl", "Uyghur Cyrillic (UKY)", arabic_to_cyrillic),
        "yengi": ("Latn", "Uyghur New Script (UYY)", arabic_to_new_script),
    }
    generated = []
    for case in cases:
        if case["expected_language"] != "ug" or case["script"] != "Arab":
            continue
        for variant, (script, alphabet, converter) in variants.items():
            converted = converter(case["text"])
            source = dict(case["source"])
            source["transliteration"] = {
                "from": "Uyghur Arabic (UEY)",
                "to": alphabet,
                "method": "deterministic alphabet mapping",
            }
            generated.append(
                {
                    **case,
                    "id": case["id"].replace("ug-", f"ug-{variant}-", 1),
                    "script": script,
                    "alphabet": alphabet,
                    "text": converted,
                    "source": source,
                }
            )
    return generated


def build_northern_pashto_cases(html: str) -> list[dict]:
    parser = ParagraphExtractor()
    parser.feed(html)
    all_words = " ".join(parser.paragraphs).split()
    held_out_words = all_words[1_000:]
    specifications = [
        (word_count, case_number)
        for word_count in TARGET_LENGTHS
        for case_number in range(1, CASES_PER_LENGTH + 1)
    ]
    rng = random.Random(f"{RANDOM_SEED}:pbu_Arab:heldout")
    rng.shuffle(specifications)
    cursor = 0
    used_texts: set[str] = set()
    selected = []
    for word_count, case_number in specifications:
        gap = rng.randint(0, 3)
        cursor += gap
        end = cursor + word_count
        text = " ".join(held_out_words[cursor:end])
        while text in used_texts and end < len(held_out_words):
            cursor += 1
            end += 1
            text = " ".join(held_out_words[cursor:end])
        if end > len(held_out_words):
            raise ValueError("Northern Pashto held-out source is too short")
        used_texts.add(text)
        selected.append(
            {
                "id": f"ps-pbu-{word_count:03}w-{case_number:02}",
                "expected_language": "ps",
                "language_name": "Pashto",
                "script": "Arab",
                "variety": "Northern",
                "word_count": word_count,
                "text": text,
                "source": {
                    "dataset": "UDHR",
                    "split": "heldout_after_training_prefix",
                    "language_code": "pbu",
                    "source_url": NORTHERN_PASHTO_URL,
                    "source_commit": UDHR_COMMIT,
                    "token_start": 1_001 + cursor,
                    "token_end": 1_000 + end,
                },
            }
        )
        cursor = end
    return sorted(selected, key=lambda case: case["id"])


def build_regional_udhr_cases(html: str, specification: dict) -> list[dict]:
    """Build non-overlapping held-out cases after a 1,000-token profile prefix."""
    parser = ParagraphExtractor()
    parser.feed(html)
    held_out_words = " ".join(parser.paragraphs).split()[1_000:]
    specifications = [
        (word_count, case_number)
        for word_count in TARGET_LENGTHS
        for case_number in range(1, specification["cases_per_length"] + 1)
    ]
    rng = random.Random(
        f"{RANDOM_SEED}:{specification['source_code']}:heldout"
    )
    rng.shuffle(specifications)
    cursor = 0
    selected = []
    for word_count, case_number in specifications:
        end = cursor + word_count
        if end > len(held_out_words):
            raise ValueError(
                f"{specification['source_code']} held-out source is too short"
            )
        selected.append(
            {
                "id": (
                    f"{specification['case_prefix']}-{word_count:03}w-"
                    f"{case_number:02}"
                ),
                "expected_language": specification["expected_language"],
                "language_name": specification["language_name"],
                "script": specification["script"],
                "alphabet": None,
                "variety": specification["variety"],
                "word_count": word_count,
                "text": " ".join(held_out_words[cursor:end]),
                "source": {
                    "dataset": "UDHR",
                    "split": "heldout_after_training_prefix",
                    "language_code": specification["source_code"],
                    "source_url": specification["source_url"],
                    "source_commit": UDHR_COMMIT,
                    "token_start": 1_001 + cursor,
                    "token_end": 1_000 + end,
                },
            }
        )
        cursor = end
    return sorted(selected, key=lambda case: case["id"])


def build_cyrillic_uzbek_cases(compressed_data: bytes) -> list[dict]:
    actual_hash = hashlib.sha256(compressed_data).hexdigest()
    if actual_hash != TATOEBA_UZBEK_SHA256:
        raise ValueError(
            "Tatoeba Uzbek SHA-256 mismatch: "
            f"expected {TATOEBA_UZBEK_SHA256}, got {actual_hash}"
        )
    rows = []
    for line in bz2.decompress(compressed_data).decode("utf-8").splitlines():
        sentence_id, language_code, text = line.split("\t", maxsplit=2)
        script_counts = Counter(
            "Cyrl" if "CYRILLIC" in unicodedata.name(character, "") else "Other"
            for character in text
            if character.isalpha()
        )
        if script_counts["Cyrl"] > script_counts["Other"]:
            rows.append((int(sentence_id), unicodedata.normalize("NFC", text)))

    texts = [text for _, text in rows]
    used_starts: set[int] = set()
    used_texts: set[str] = set()
    cases = []
    for word_count in TARGET_LENGTHS:
        rng = random.Random(f"{RANDOM_SEED}:tatoeba:uzb_Cyrl:{word_count}")
        for case_number in range(1, CASES_PER_LENGTH + 1):
            text, sentence_start, sentence_end = choose_window(
                texts, word_count, rng, used_starts, used_texts
            )
            cases.append(
                {
                    "id": f"uz-cyrl-{word_count:03}w-{case_number:02}",
                    "expected_language": "uz",
                    "language_name": "Uzbek",
                    "script": "Cyrl",
                    "variety": "Northern",
                    "word_count": word_count,
                    "text": text,
                    "source": {
                        "dataset": "Tatoeba",
                        "split": "per_language_export",
                        "language_code": "uzb",
                        "source_url": TATOEBA_UZBEK_URL,
                        "archive_sha256": TATOEBA_UZBEK_SHA256,
                        "sentence_ids": [
                            sentence_id
                            for sentence_id, _ in rows[
                                sentence_start - 1 : sentence_end
                            ]
                        ],
                    },
                }
            )
    return cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use an existing flores200_dataset.tar.gz instead of downloading it",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with tempfile.TemporaryDirectory(prefix="lingo-detect-flores-") as temporary:
        archive_path = args.archive or Path(temporary) / "flores200_dataset.tar.gz"
        if not args.archive:
            print(f"Downloading {ARCHIVE_URL}")
            download_archive(archive_path)
        actual_hash = sha256(archive_path)
        if actual_hash != ARCHIVE_SHA256:
            raise ValueError(
                f"archive SHA-256 mismatch: expected {ARCHIVE_SHA256}, got {actual_hash}"
            )
        cases = build_cases(archive_path)
        cases.extend(build_transliterated_uighur_cases(cases))
        cases.extend(build_nigerian_pidgin_cases(download_bytes(NAIJA_NSC_TEST_URL)))
        cases.extend(build_cyrillic_uzbek_cases(download_bytes(TATOEBA_UZBEK_URL)))
        cases.extend(build_northern_pashto_cases(download_text(NORTHERN_PASHTO_URL)))
        for specification in REGIONAL_UDHR_SOURCES:
            cases.extend(
                build_regional_udhr_cases(
                    download_text(specification["source_url"]), specification
                )
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    print(f"Wrote {len(cases)} cases to {OUTPUT}")


if __name__ == "__main__":
    main()
