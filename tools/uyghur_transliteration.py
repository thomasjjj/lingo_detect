"""Deterministic modern-Uyghur alphabet conversions used by data builders.

The source side is the Uyghur Arabic alphabet (UEY).  The targets cover the
modern auxiliary Latin alphabet (ULY), Central Asian Cyrillic (UKY), and the
legacy Latin-derived Uyghur New Script (UYY).  These converters deliberately
preserve punctuation and unknown characters so generated fixtures remain
traceable to their source text.
"""

from __future__ import annotations

import unicodedata


ARABIC_TO_LATIN = str.maketrans(
    {
        "ئ": "",
        "ا": "a",
        "ە": "e",
        "ب": "b",
        "پ": "p",
        "ت": "t",
        "ج": "j",
        "چ": "ch",
        "خ": "x",
        "د": "d",
        "ر": "r",
        "ز": "z",
        "ژ": "zh",
        "س": "s",
        "ش": "sh",
        "غ": "gh",
        "ف": "f",
        "ق": "q",
        "ك": "k",
        "گ": "g",
        "ڭ": "ng",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ھ": "h",
        "و": "o",
        "ۇ": "u",
        "ۆ": "ö",
        "ۈ": "ü",
        "ۋ": "w",
        "ې": "ë",
        "ى": "i",
        "ي": "y",
    }
)

ARABIC_TO_CYRILLIC = str.maketrans(
    {
        "ئ": "",
        "ا": "а",
        "ە": "ә",
        "ب": "б",
        "پ": "п",
        "ت": "т",
        "ج": "җ",
        "چ": "ч",
        "خ": "х",
        "د": "д",
        "ر": "р",
        "ز": "з",
        "ژ": "ж",
        "س": "с",
        "ش": "ш",
        "غ": "ғ",
        "ف": "ф",
        "ق": "қ",
        "ك": "к",
        "گ": "г",
        "ڭ": "ң",
        "ل": "л",
        "م": "м",
        "ن": "н",
        "ھ": "һ",
        "و": "о",
        "ۇ": "у",
        "ۆ": "ө",
        "ۈ": "ү",
        "ۋ": "в",
        "ې": "е",
        "ى": "и",
        "ي": "й",
    }
)

ARABIC_TO_NEW_SCRIPT = str.maketrans(
    {
        "ئ": "",
        "ا": "a",
        "ە": "ə",
        "ب": "b",
        "پ": "p",
        "ت": "t",
        "ج": "j",
        "چ": "q",
        "خ": "h",
        "د": "d",
        "ر": "r",
        "ز": "z",
        "ژ": "ⱬ",
        "س": "s",
        "ش": "x",
        "غ": "ƣ",
        "ف": "f",
        "ق": "ⱪ",
        "ك": "k",
        "گ": "g",
        "ڭ": "ng",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ھ": "ⱨ",
        "و": "o",
        "ۇ": "u",
        "ۆ": "ɵ",
        "ۈ": "ü",
        "ۋ": "w",
        "ې": "e",
        "ى": "i",
        "ي": "y",
    }
)


def _normalise_arabic(text: str) -> str:
    """Fold presentation forms while retaining standard Uyghur letters."""
    return unicodedata.normalize("NFKC", text)


def arabic_to_latin(text: str) -> str:
    """Convert UEY text to the current Uyghur Latin alphabet (ULY/NUL)."""
    return _normalise_arabic(text).translate(ARABIC_TO_LATIN)


def arabic_to_cyrillic(text: str) -> str:
    """Convert UEY text to the Central Asian Uyghur Cyrillic alphabet."""
    converted = _normalise_arabic(text).translate(ARABIC_TO_CYRILLIC)
    # Cyrillic Uyghur has dedicated iotated vowel letters for these sequences.
    return converted.replace("йа", "я").replace("йу", "ю").replace("йо", "ё")


def arabic_to_new_script(text: str) -> str:
    """Convert UEY text to the legacy Latin-derived Uyghur New Script."""
    return _normalise_arabic(text).translate(ARABIC_TO_NEW_SCRIPT)
