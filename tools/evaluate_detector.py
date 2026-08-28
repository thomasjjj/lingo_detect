"""Evaluate a detector callable against the held-out language cases."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "tests" / "data" / "flores200_devtest.jsonl"
UNKNOWN_LANGUAGE_CODES = {"", "und", "unknown", "uncertain"}
SCRIPT_ALIASES = {
    "arab": "Arab",
    "arabic": "Arab",
    "armn": "Armn",
    "armenian": "Armn",
    "cyrl": "Cyrl",
    "cyrillic": "Cyrl",
    "geor": "Geor",
    "georgian": "Geor",
    "hebr": "Hebr",
    "hebrew": "Hebr",
    "latn": "Latn",
    "latin": "Latn",
}
LANGUAGE_SCRIPTS = {
    "ar": "Arab",
    "en": "Latn",
    "fa": "Arab",
    "he": "Hebr",
    "hy": "Armn",
    "ka": "Geor",
    "kk": "Cyrl",
    "ky": "Cyrl",
    "pa": "Arab",
    "ps": "Arab",
    "ru": "Cyrl",
    "sd": "Arab",
    "tg": "Cyrl",
    "tr": "Latn",
    "uk": "Cyrl",
    "ur": "Arab",
    "yi": "Hebr",
    # Azerbaijani, Kurdish, Turkmen, Uyghur, and Uzbek are deliberately omitted
    # because multiple scripts are supported for each language.
}


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def load_detector(specification: str) -> Callable[[str], Any]:
    module_name, separator, attribute_name = specification.partition(":")
    if not separator or not module_name or not attribute_name:
        raise ValueError("detector must use the form package.module:function")
    # Make the source checkout runnable without requiring an editable install.
    root_string = str(ROOT)
    if root_string not in sys.path:
        sys.path.insert(0, root_string)
    module = importlib.import_module(module_name)
    detector = getattr(module, attribute_name)
    if not callable(detector):
        raise TypeError(f"{specification} is not callable")
    return detector


def value_from_result(result: Any, names: tuple[str, ...]) -> Any:
    if isinstance(result, Mapping):
        for name in names:
            if name in result:
                return result[name]
    for name in names:
        if hasattr(result, name):
            return getattr(result, name)
    return None


def normalise_script(value: Any) -> str | None:
    if value is None:
        return None
    return SCRIPT_ALIASES.get(str(value).strip().lower(), str(value))


def normalise_language(value: Any) -> str | None:
    if value is None:
        return None
    code = str(value).strip().lower()
    return None if code in UNKNOWN_LANGUAGE_CODES else code


def parse_prediction(result: Any) -> dict[str, str | None]:
    if isinstance(result, str):
        script = normalise_script(result)
        if result.strip().lower() in SCRIPT_ALIASES:
            return {"language_code": None, "script": script}
        language = normalise_language(result)
        return {
            "language_code": language,
            "script": LANGUAGE_SCRIPTS.get(language or ""),
        }

    if isinstance(result, (tuple, list)) and result:
        language = normalise_language(result[0])
        # A second tuple/list item is commonly a confidence score, so script
        # metadata is only read from named fields on structured results.
        script = None
    else:
        language = normalise_language(
            value_from_result(result, ("language_code", "language", "code"))
        )
        script = normalise_script(
            value_from_result(result, ("script", "alphabet", "script_code"))
        )
    if language is None and script is None:
        raise TypeError(
            "detector result must expose a language_code and/or script/alphabet"
        )
    return {
        "language_code": language,
        "script": script or LANGUAGE_SCRIPTS.get(language or ""),
    }


def language_code(result: Any) -> str:
    """Compatibility helper for detectors that are expected to resolve a language."""
    code = parse_prediction(result)["language_code"]
    return code or "und"


def percentage(correct: int, total: int) -> str:
    return f"{correct / total:.1%}" if total else "n/a"


def evaluate(cases: list[dict], detector: Callable[[str], Any]) -> dict:
    rows = []
    started = time.perf_counter()
    for case in cases:
        prediction = parse_prediction(detector(case["text"]))
        predicted = prediction["language_code"]
        language_correct = predicted == case["expected_language"]
        script_correct = prediction["script"] == case["script"]
        if language_correct and script_correct:
            resolution = "language"
        elif predicted is None and script_correct:
            resolution = "script"
        else:
            resolution = "wrong"
        rows.append(
            {
                **case,
                "predicted_language": predicted,
                "predicted_script": prediction["script"],
                "language_correct": language_correct,
                "script_correct": script_correct,
                "resolution": resolution,
            }
        )
    elapsed = time.perf_counter() - started
    return {"rows": rows, "elapsed_seconds": elapsed}


def print_report(evaluation: dict) -> None:
    rows = evaluation["rows"]
    exact = sum(row["resolution"] == "language" for row in rows)
    script_only = sum(row["resolution"] == "script" for row in rows)
    wrong = len(rows) - exact - script_only
    language_predictions = sum(row["predicted_language"] is not None for row in rows)
    script_correct = sum(row["script_correct"] for row in rows)
    print(f"exact language: {exact}/{len(rows)} ({percentage(exact, len(rows))})")
    print(
        f"script-only fallback: {script_only}/{len(rows)} "
        f"({percentage(script_only, len(rows))})"
    )
    print(
        f"useful resolution: {exact + script_only}/{len(rows)} "
        f"({percentage(exact + script_only, len(rows))})"
    )
    print(f"wrong: {wrong}/{len(rows)} ({percentage(wrong, len(rows))})")
    print(
        f"language coverage: {language_predictions}/{len(rows)} "
        f"({percentage(language_predictions, len(rows))})"
    )
    print(
        f"language accuracy when attempted: {exact}/{language_predictions} "
        f"({percentage(exact, language_predictions)})"
    )
    print(
        f"script accuracy: {script_correct}/{len(rows)} "
        f"({percentage(script_correct, len(rows))})"
    )
    print(f"elapsed: {evaluation['elapsed_seconds']:.3f}s")

    groupings = (
        ("word count", lambda row: row["word_count"]),
        ("language", lambda row: row["expected_language"]),
        (
            "language/script",
            lambda row: f"{row['expected_language']}/{row['script']}",
        ),
        (
            "language/variety",
            lambda row: (
                f"{row['expected_language']}/{row['variety']}"
                if row.get("variety")
                else None
            ),
        ),
        (
            "language/alphabet",
            lambda row: (
                f"{row['expected_language']}/{row['alphabet']}"
                if row.get("alphabet")
                else None
            ),
        ),
    )
    for heading, key_function in groupings:
        grouped: dict[Any, list[dict]] = defaultdict(list)
        for row in rows:
            value = key_function(row)
            if value is not None:
                grouped[value].append(row)
        print(f"\nby {heading}:")
        for value in sorted(grouped):
            group = grouped[value]
            group_exact = sum(row["resolution"] == "language" for row in group)
            group_script = sum(row["resolution"] == "script" for row in group)
            group_wrong = len(group) - group_exact - group_script
            print(
                f"  {str(value):>4}: language={group_exact:>3}, "
                f"script={group_script:>3}, wrong={group_wrong:>3}"
            )

    errors = Counter(
        (row["expected_language"], row["predicted_language"] or "und")
        for row in rows
        if row["resolution"] == "wrong"
    )
    print("\nconfusions:")
    if not errors:
        print("  none")
    for (expected, predicted), count in errors.most_common():
        print(f"  {expected} -> {predicted}: {count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--detector",
        default="lingo_detect:detect",
        help="Detector callable as package.module:function (default: %(default)s)",
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    try:
        detector = load_detector(args.detector)
    except (ImportError, AttributeError, TypeError, ValueError) as error:
        raise SystemExit(f"Cannot load detector {args.detector!r}: {error}") from error
    print_report(evaluate(load_cases(args.cases), detector))


if __name__ == "__main__":
    main()
