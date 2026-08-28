"""Build small, parallel language samples from the UDHR corpus.

The source files are pinned to a specific revision of ``wooorm/udhr``. Each
sample contains the first 1,000 whitespace-delimited tokens found in paragraph
elements; document titles and article-number headings are deliberately omitted.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError

try:
    from .uyghur_transliteration import arabic_to_cyrillic, arabic_to_new_script
except ImportError:  # Support ``python tools/build_samples.py``.
    from uyghur_transliteration import arabic_to_cyrillic, arabic_to_new_script


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "corpora"
TARGET_WORDS = 1_000
SOURCE_REPOSITORY = "https://github.com/wooorm/udhr"
SOURCE_COMMIT = "d3d38276c91668df9ac4e33e5dac7cd3a14c12b2"
RAW_ROOT = f"https://raw.githubusercontent.com/wooorm/udhr/{SOURCE_COMMIT}/declaration"
USER_AGENT = "lingo-detect-corpus-builder/0.1 (educational language research)"

# Uzbek has two actively encountered writing systems. Both samples should map
# to the same ISO 639-1 language code even though their script signals differ.
LANGUAGES = {
    "arabic": {"code": "ar", "files": {"sample.txt": "arb.html"}},
    "armenian": {"code": "hy", "files": {"sample.txt": "hye.html"}},
    "azerbaijani": {
        "code": "az",
        "files": {
            "sample.txt": "azj_latn.html",
            "sample_cyrl.txt": "azj_cyrl.html",
        },
    },
    "english": {"code": "en", "files": {"sample.txt": "eng.html"}},
    "georgian": {"code": "ka", "files": {"sample.txt": "kat.html"}},
    "hebrew": {"code": "he", "files": {"sample.txt": "heb.html"}},
    "kazakh": {"code": "kk", "files": {"sample.txt": "kaz.html"}},
    "kurdish": {"code": "ku", "files": {"sample_latn.txt": "kmr.html"}},
    "kyrgyz": {"code": "ky", "files": {"sample.txt": "kir.html"}},
    "persian": {"code": "fa", "files": {"sample.txt": "pes_1.html"}},
    "pashto": {"code": "ps", "files": {"sample.txt": "pbu.html"}},
    "punjabi": {"code": "pa", "files": {"sample.txt": "pnb.html"}},
    "russian": {"code": "ru", "files": {"sample.txt": "rus.html"}},
    "tajik": {"code": "tg", "files": {"sample.txt": "tgk.html"}},
    "turkish": {"code": "tr", "files": {"sample.txt": "tur.html"}},
    "turkmen": {
        "code": "tk",
        "files": {
            "sample.txt": "tuk_latn.html",
            "sample_cyrl.txt": "tuk_cyrl.html",
        },
    },
    "ukrainian": {"code": "uk", "files": {"sample.txt": "ukr.html"}},
    "urdu": {"code": "ur", "files": {"sample.txt": "urd.html"}},
    "uyghur": {
        "code": "ug",
        "files": {
            "sample.txt": "uig_arab.html",
            "sample_latn.txt": "uig_latn.html",
        },
    },
    "uzbek": {
        "code": "uz",
        "files": {
            "sample.txt": "uzn_latn.html",
            "sample_cyrl.txt": "uzn_cyrl.html",
        },
    },
    "yiddish": {"code": "yi", "files": {"sample.txt": "ydd.html"}},
}


class ParagraphExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_paragraph = False
        self._parts: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "p":
            self._in_paragraph = True
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._in_paragraph:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self._in_paragraph:
            text = re.sub(r"\s+", " ", "".join(self._parts)).strip()
            if text:
                self.paragraphs.append(text)
            self._in_paragraph = False
            self._parts = []


def download_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except (HTTPError, URLError):
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("unreachable")


def extract_sample(html: str) -> tuple[str, int]:
    parser = ParagraphExtractor()
    parser.feed(html)
    text = "\n\n".join(parser.paragraphs)
    words = list(re.finditer(r"\S+", text))
    if len(words) < TARGET_WORDS:
        raise ValueError(f"only {len(words)} words available; need {TARGET_WORDS}")
    sample = text[: words[TARGET_WORDS - 1].end()].strip() + "\n"
    return sample, len(words)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--language",
        choices=sorted(LANGUAGES),
        help="Build one corpus directory instead of rebuilding every language",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    selected = (
        {args.language: LANGUAGES[args.language]} if args.language else LANGUAGES
    )
    for directory_name, language in selected.items():
        destination = CORPORA / directory_name
        destination.mkdir(parents=True, exist_ok=True)
        sources = []
        for output_name, source_name in language["files"].items():
            source_url = f"{RAW_ROOT}/{source_name}"
            sample, source_word_count = extract_sample(download_text(source_url))
            (destination / output_name).write_text(sample, encoding="utf-8")
            sources.append(
                {
                    "sample_file": output_name,
                    "sample_word_count": len(sample.split()),
                    "source_file": source_name,
                    "source_word_count": source_word_count,
                    "url": source_url,
                }
            )

        if directory_name == "uyghur":
            arabic_sample = (destination / "sample.txt").read_text(encoding="utf-8")
            generated_samples = {
                "sample_cyrl.txt": (
                    arabic_to_cyrillic(arabic_sample),
                    "Uyghur Arabic (UEY) to Uyghur Cyrillic (UKY)",
                ),
                "sample_yengi.txt": (
                    arabic_to_new_script(arabic_sample),
                    "Uyghur Arabic (UEY) to Uyghur New Script (UYY)",
                ),
            }
            for output_name, (sample, transformation) in generated_samples.items():
                (destination / output_name).write_text(sample, encoding="utf-8")
                sources.append(
                    {
                        "sample_file": output_name,
                        "sample_word_count": len(sample.split()),
                        "generated_from": "sample.txt",
                        "transformation": transformation,
                    }
                )

        metadata = {
            "language": directory_name,
            "language_code": language["code"],
            "retrieved_at": retrieved_at,
            "source": "Universal Declaration of Human Rights",
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": SOURCE_COMMIT,
            "upstream_source": "Office of the UN High Commissioner for Human Rights",
            "license": "The source package is MIT licensed and describes the UDHR as copyright-free",
            "modified": (
                "Extracted HTML paragraph text and truncated to 1,000 whitespace "
                "tokens; Uyghur Cyrillic and New Script samples were generated "
                "from the Arabic sample with deterministic alphabet mappings"
                if directory_name == "uyghur"
                else "Extracted HTML paragraph text and truncated to 1,000 whitespace tokens"
            ),
            "samples": sources,
        }
        (destination / "sources.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        counts = ", ".join(
            f"{source['sample_file']}={source['sample_word_count']}" for source in sources
        )
        print(f"{directory_name:10} {counts}")


if __name__ == "__main__":
    main()
