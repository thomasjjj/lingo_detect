"""Build profile corpora from FLORES-200's dev split.

These samples cover regional varieties absent from the parallel UDHR checkout.
The separate FLORES devtest split remains reserved for evaluation.
"""

from __future__ import annotations

import argparse
import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    from .build_test_samples import (
        ARCHIVE_SHA256,
        ARCHIVE_URL,
        download_archive,
        read_language_lines,
        sha256,
    )
except ImportError:  # Support ``python tools/build_flores_samples.py``.
    from build_test_samples import (
        ARCHIVE_SHA256,
        ARCHIVE_URL,
        download_archive,
        read_language_lines,
        sha256,
    )


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "corpora"
TARGET_WORDS = 1_000

SAMPLES = {
    "arabic": {
        "sample_acm.txt": ("ar", "acm_Arab", "Mesopotamian Arabic"),
        "sample_acq.txt": ("ar", "acq_Arab", "Ta’izzi-Adeni Arabic"),
        "sample_ajp.txt": ("ar", "ajp_Arab", "South Levantine Arabic"),
        "sample_apc.txt": ("ar", "apc_Arab", "North Levantine Arabic"),
        "sample_ars.txt": ("ar", "ars_Arab", "Najdi Arabic"),
        "sample_arz.txt": ("ar", "arz_Arab", "Egyptian Arabic"),
    },
    "azerbaijani": {
        "sample_arab.txt": ("az", "azb_Arab", "South Azerbaijani"),
    },
    "kurdish": {
        "sample.txt": ("ku", "ckb_Arab", "Central Kurdish (Sorani)"),
    },
    "persian": {
        "sample_dari.txt": ("fa", "prs_Arab", "Dari"),
    },
    "sindhi": {
        "sample.txt": ("sd", "snd_Arab", "Sindhi"),
    },
}


def first_words(lines: list[str]) -> str:
    words = "\n\n".join(lines).split()
    if len(words) < TARGET_WORDS:
        raise ValueError(f"only {len(words)} words available; need {TARGET_WORDS}")
    return " ".join(words[:TARGET_WORDS]) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use an existing flores200_dataset.tar.gz instead of downloading it",
    )
    parser.add_argument(
        "--language",
        choices=sorted(SAMPLES),
        help="Build one corpus directory instead of every configured directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    selected = {args.language: SAMPLES[args.language]} if args.language else SAMPLES
    with tempfile.TemporaryDirectory(prefix="lingo-detect-flores-corpora-") as temporary:
        archive_path = args.archive or Path(temporary) / "flores200_dataset.tar.gz"
        if not args.archive:
            print(f"Downloading {ARCHIVE_URL}")
            download_archive(archive_path)
        actual_hash = sha256(archive_path)
        if actual_hash != ARCHIVE_SHA256:
            raise ValueError(
                f"archive SHA-256 mismatch: expected {ARCHIVE_SHA256}, got {actual_hash}"
            )

        with tarfile.open(archive_path, mode="r:gz") as archive:
            for directory_name, samples in selected.items():
                destination = CORPORA / directory_name
                destination.mkdir(parents=True, exist_ok=True)
                sources = []
                for output_name, (language_code, flores_code, variety) in samples.items():
                    sample = first_words(
                        read_language_lines(archive, flores_code, split="dev")
                    )
                    (destination / output_name).write_text(sample, encoding="utf-8")
                    sources.append(
                        {
                            "sample_file": output_name,
                            "sample_word_count": len(sample.split()),
                            "language_code": language_code,
                            "variety": variety,
                            "flores_code": flores_code,
                        }
                    )

                metadata = {
                    "language": directory_name,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                    "source": "FLORES-200",
                    "split": "dev",
                    "archive_url": ARCHIVE_URL,
                    "archive_sha256": ARCHIVE_SHA256,
                    "license": "CC BY-SA 4.0",
                    "modified": "Joined dev sentences and truncated to 1,000 whitespace tokens",
                    "samples": sources,
                }
                metadata_name = (
                    "sources_flores.json"
                    if directory_name
                    in {"arabic", "azerbaijani", "kurdish", "persian"}
                    else "sources.json"
                )
                (destination / metadata_name).write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                counts = ", ".join(
                    f"{source['sample_file']}={source['sample_word_count']}"
                    for source in sources
                )
                print(f"{directory_name:12} {counts}")


if __name__ == "__main__":
    main()
