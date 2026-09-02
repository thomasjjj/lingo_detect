"""Print compact character and word statistics for the corpus samples."""

from __future__ import annotations

import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from .build_language_profiles import tokens as tokenize
except ImportError:  # Support ``python tools/analyze_samples.py``.
    from build_language_profiles import tokens as tokenize


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "corpora"


def script_of(character: str) -> str:
    name = unicodedata.name(character, "")
    if "ARABIC" in name:
        return "Arabic"
    if "ARMENIAN" in name:
        return "Armenian"
    if "BENGALI" in name:
        return "Bengali"
    if "CYRILLIC" in name:
        return "Cyrillic"
    if "DEVANAGARI" in name:
        return "Devanagari"
    if "GEORGIAN" in name:
        return "Georgian"
    if "HEBREW" in name:
        return "Hebrew"
    if "HIRAGANA" in name or "KATAKANA" in name:
        return "Japanese"
    if "LATIN" in name:
        return "Latin"
    if "TELUGU" in name:
        return "Telugu"
    if "CJK" in name:
        return "Han"
    return "Other"


def label(path: Path) -> str:
    suffixes = {
        "sample_cyrl": "/cyrl",
        "sample_latn": "/latn",
        "sample_yengi": "/yengi",
    }
    suffix = suffixes.get(path.stem)
    if suffix is None:
        suffix = (
            f"/{path.stem.removeprefix('sample_')}"
            if path.stem.startswith("sample_")
            else ""
        )
    return f"{path.parent.name}{suffix}"


def format_counts(counts: Counter[str], limit: int) -> str:
    return " ".join(f"{item}:{count}" for item, count in counts.most_common(limit))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    paths = sorted(CORPORA.glob("*/sample*.txt"))
    texts = {
        label(path): unicodedata.normalize("NFC", path.read_text(encoding="utf-8")).casefold()
        for path in paths
    }
    letter_counts = {
        name: Counter(character for character in text if character.isalpha())
        for name, text in texts.items()
    }
    tokens = {name: tokenize(text) for name, text in texts.items()}
    word_counts = {name: Counter(words) for name, words in tokens.items()}

    for name in texts:
        letters = letter_counts[name]
        scripts = Counter()
        for character, count in letters.items():
            scripts[script_of(character)] += count
        dominant = scripts.most_common(1)[0][0]
        peers = [
            other
            for other in texts
            if other != name
            and Counter(
                script_of(character) for character in letter_counts[other].elements()
            ).most_common(1)[0][0]
            == dominant
        ]
        peer_letters = set().union(*(letter_counts[other] for other in peers))
        exclusive = Counter(
            {
                character: count
                for character, count in letters.items()
                if character not in peer_letters
            }
        )
        script_total = sum(scripts.values())
        shares = ", ".join(
            f"{script}={count / script_total:.1%}" for script, count in scripts.most_common()
        )
        print(f"[{name}] letters={sum(letters.values())}; {shares}")
        bigrams = Counter(zip(tokens[name], tokens[name][1:]))
        formatted_bigrams = " ".join(
            f"{' '.join(items)}:{count}" for items, count in bigrams.most_common(8)
        )
        print(f"  observed-exclusive-letters: {format_counts(exclusive, 20) or '-'}")
        print(f"  top-words: {format_counts(word_counts[name], 15)}")
        print(f"  top-bigrams: {formatted_bigrams}")

    diagnostic_characters = {
        "Arabic-script": "ةأإآؤئءىكکيیۀپچژگٹڈڑںھہےټځڅډړږښګڼېۍەڭۆۇۈۋ",
        "Hebrew-script": "ךםןףץװױײ",
        "Cyrillic-script": "ёыэъщцґєіїғӣқӯҳҷўәҗңөүһ",
        "Latin-script": "qwxʻʼëéöüçğışəƣɵⱨⱪⱬ",
    }
    print("\n[diagnostic-character-counts]")
    for group, characters in diagnostic_characters.items():
        print(f"  {group}")
        for name, counts in letter_counts.items():
            present = " ".join(f"{char}:{counts[char]}" for char in characters if counts[char])
            if present:
                print(f"    {name}: {present}")


if __name__ == "__main__":
    main()
