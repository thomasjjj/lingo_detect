"""Print compact character and word statistics for the corpus samples."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "corpora"
TOKEN = re.compile(r"[^\W\d_]+(?:[‘’ʼ'][^\W\d_]+)*", re.UNICODE)


def script_of(character: str) -> str:
    name = unicodedata.name(character, "")
    if "ARABIC" in name:
        return "Arabic"
    if "CYRILLIC" in name:
        return "Cyrillic"
    if "LATIN" in name:
        return "Latin"
    return "Other"


def label(path: Path) -> str:
    suffixes = {
        "sample_cyrl": "/cyrl",
        "sample_latn": "/latn",
        "sample_yengi": "/yengi",
    }
    suffix = suffixes.get(path.stem, "")
    return f"{path.parent.name}{suffix}"


def format_counts(counts: Counter[str], limit: int) -> str:
    return " ".join(f"{item}:{count}" for item, count in counts.most_common(limit))


def main() -> None:
    paths = sorted(CORPORA.glob("*/sample*.txt"))
    texts = {
        label(path): unicodedata.normalize("NFC", path.read_text(encoding="utf-8")).casefold()
        for path in paths
    }
    letter_counts = {
        name: Counter(character for character in text if character.isalpha())
        for name, text in texts.items()
    }
    tokens = {name: TOKEN.findall(text) for name, text in texts.items()}
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
        "Arabic-script": "ةأإآؤئءىپچژگٹڈڑںھہےټځڅډړږښګڼېۍەڭۆۇۈۋ",
        "Cyrillic-script": "ёыэъщцґєіїғӣқӯҳҷўәҗңөүһ",
        "Latin-script": "qwxʻʼëéöüəƣɵⱨⱪⱬ",
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
