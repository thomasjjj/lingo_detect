"""Build deterministic held-out language-identification cases from FLORES-200."""

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


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "data" / "flores200_devtest.jsonl"
ARCHIVE_URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"
ARCHIVE_SHA256 = "b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6"
RANDOM_SEED = 20260828
TARGET_LENGTHS = (1, 2, 3, 5, 10, 20, 50, 100)
CASES_PER_LENGTH = 5
USER_AGENT = "lingo-detect-test-builder/0.1 (educational language research)"
UDHR_COMMIT = "d3d38276c91668df9ac4e33e5dac7cd3a14c12b2"
NORTHERN_PASHTO_URL = (
    "https://raw.githubusercontent.com/wooorm/udhr/"
    f"{UDHR_COMMIT}/declaration/pbu.html"
)
TATOEBA_UZBEK_URL = (
    "https://downloads.tatoeba.org/exports/per_language/uzb/uzb_sentences.tsv.bz2"
)
TATOEBA_UZBEK_SHA256 = (
    "3fb90d8e219e7580b0779ee7dc8701a456a21e2b1d01fe52eed1ca7b0c664283"
)

LANGUAGES = {
    "ar": {"name": "Arabic", "flores": "arb_Arab", "script": "Arab"},
    "en": {"name": "English", "flores": "eng_Latn", "script": "Latn"},
    "ps": {
        "name": "Pashto",
        "flores": "pbt_Arab",
        "script": "Arab",
        "variety": "Southern",
    },
    "ru": {"name": "Russian", "flores": "rus_Cyrl", "script": "Cyrl"},
    "tg": {"name": "Tajik", "flores": "tgk_Cyrl", "script": "Cyrl"},
    "uk": {"name": "Ukrainian", "flores": "ukr_Cyrl", "script": "Cyrl"},
    "ur": {"name": "Urdu", "flores": "urd_Arab", "script": "Arab"},
    "uz": {
        "name": "Uzbek",
        "flores": "uzn_Latn",
        "script": "Latn",
        "variety": "Northern",
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


def read_language_lines(archive: tarfile.TarFile, flores_code: str) -> list[str]:
    member_name = f"./flores200_dataset/devtest/{flores_code}.devtest"
    member = archive.getmember(member_name)
    source = archive.extractfile(member)
    if source is None:
        raise RuntimeError(f"could not read {member_name}")
    return [
        unicodedata.normalize("NFC", line.strip())
        for line in source.read().decode("utf-8").splitlines()
        if line.strip()
    ]


def choose_window(
    lines: list[str],
    word_count: int,
    rng: random.Random,
    used_starts: set[int],
    used_texts: set[str],
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
        used_starts.add(line_index)
        used_texts.add(text)
        return text, line_index + 1, final_line_index + 1
    raise RuntimeError(f"could not select a unique {word_count}-word window")


def build_cases(archive_path: Path) -> list[dict]:
    cases = []
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for language_code, language in LANGUAGES.items():
            lines = read_language_lines(archive, language["flores"])
            used_starts: set[int] = set()
            used_texts: set[str] = set()
            for word_count in TARGET_LENGTHS:
                rng = random.Random(
                    f"{RANDOM_SEED}:{language['flores']}:{word_count}"
                )
                for case_number in range(1, CASES_PER_LENGTH + 1):
                    text, sentence_start, sentence_end = choose_window(
                        lines, word_count, rng, used_starts, used_texts
                    )
                    cases.append(
                        {
                            "id": f"{language_code}-{word_count:03}w-{case_number:02}",
                            "expected_language": language_code,
                            "language_name": language["name"],
                            "script": language["script"],
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
        cases.extend(build_cyrillic_uzbek_cases(download_bytes(TATOEBA_UZBEK_URL)))
        cases.extend(build_northern_pashto_cases(download_text(NORTHERN_PASHTO_URL)))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in cases),
        encoding="utf-8",
    )
    print(f"Wrote {len(cases)} cases to {OUTPUT}")


if __name__ == "__main__":
    main()
