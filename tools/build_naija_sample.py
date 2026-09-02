"""Build the Nigerian Pidgin profile corpus from pinned NaijaSynCor data."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from .build_test_samples import (
        NAIJA_NSC_COMMIT,
        NAIJA_NSC_TRAIN_SHA256,
        NAIJA_NSC_TRAIN_URL,
        download_bytes,
        read_naija_texts,
    )
except ImportError:  # Support ``python tools/build_naija_sample.py``.
    from build_test_samples import (
        NAIJA_NSC_COMMIT,
        NAIJA_NSC_TRAIN_SHA256,
        NAIJA_NSC_TRAIN_URL,
        download_bytes,
        read_naija_texts,
    )


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "corpora" / "nigerian_pidgin"
TARGET_WORDS = 1_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        help="Use an existing pinned pcm_nsc-ud-train.conllu file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = (
        args.source.read_bytes()
        if args.source
        else download_bytes(NAIJA_NSC_TRAIN_URL)
    )
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != NAIJA_NSC_TRAIN_SHA256:
        raise ValueError(
            "NaijaSynCor train SHA-256 mismatch: "
            f"expected {NAIJA_NSC_TRAIN_SHA256}, got {actual_hash}"
        )

    texts = read_naija_texts(data)
    words = " ".join(texts).split()
    if len(words) < TARGET_WORDS:
        raise ValueError(f"only {len(words)} words available; need {TARGET_WORDS}")
    sample = " ".join(words[:TARGET_WORDS]) + "\n"

    DESTINATION.mkdir(parents=True, exist_ok=True)
    (DESTINATION / "sample.txt").write_text(sample, encoding="utf-8")
    metadata = {
        "language": "nigerian_pidgin",
        "language_code": "pcm",
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "NaijaSynCor Universal Dependencies treebank",
        "split": "train",
        "source_url": NAIJA_NSC_TRAIN_URL,
        "source_commit": NAIJA_NSC_COMMIT,
        "source_sha256": NAIJA_NSC_TRAIN_SHA256,
        "license": "CC BY-SA 4.0",
        "modified": (
            "Extracted text_ortho sentences and truncated to 1,000 whitespace tokens"
        ),
        "samples": [
            {
                "sample_file": "sample.txt",
                "sample_word_count": TARGET_WORDS,
                "source_sentence_count": len(texts),
            }
        ],
    }
    (DESTINATION / "sources.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"nigerian_pidgin sample.txt={TARGET_WORDS}")


if __name__ == "__main__":
    main()
