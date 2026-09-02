from __future__ import annotations

import json
import unicodedata
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "data" / "flores200_devtest.jsonl"
LANGUAGES = {
    "ar", "az", "bn", "de", "en", "es", "fa", "fr", "ha", "he",
    "hi", "hy", "id", "ja", "ka", "kk", "ku", "ky", "mr", "pa",
    "pcm", "ps", "pt", "ru", "sd", "sw", "te", "tg", "tk", "tr",
    "ug", "uk", "ur", "uz", "vi", "yi", "zh",
}
LENGTHS = {1, 2, 3, 5, 10, 20, 50, 100}
CASES_PER_BUCKET = 5
CASES_PER_LANGUAGE_BUCKET = {
    "ar": 35,
    "az": 12,
    "fa": 10,
    "ku": 8,
    "ps": 10,
    "tk": 6,
    "ug": 20,
    "uz": 10,
}


class EvaluationDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = [
            json.loads(line)
            for line in CASES_PATH.read_text(encoding="utf-8").splitlines()
        ]

    def test_expected_bucket_coverage(self) -> None:
        buckets = Counter(
            (case["expected_language"], case["word_count"]) for case in self.cases
        )
        expected = Counter({
            (language, length): CASES_PER_LANGUAGE_BUCKET.get(
                language, CASES_PER_BUCKET
            )
            for language in LANGUAGES
            for length in LENGTHS
        })
        self.assertEqual(buckets, expected)

    def test_pashto_varieties_and_uzbek_scripts_are_covered(self) -> None:
        pashto_varieties = Counter(
            (case["variety"], case["word_count"])
            for case in self.cases
            if case["expected_language"] == "ps"
        )
        uzbek_scripts = Counter(
            (case["script"], case["word_count"])
            for case in self.cases
            if case["expected_language"] == "uz"
        )
        expected = Counter(
            {
                (value, length): CASES_PER_BUCKET
                for value in {"Northern", "Southern"}
                for length in LENGTHS
            }
        )
        self.assertEqual(pashto_varieties, expected)
        expected_scripts = Counter(
            {
                (script, length): CASES_PER_BUCKET
                for script in {"Latn", "Cyrl"}
                for length in LENGTHS
            }
        )
        self.assertEqual(uzbek_scripts, expected_scripts)

    def test_all_supported_uighur_alphabets_are_covered(self) -> None:
        uighur_alphabets = Counter(
            (case["alphabet"], case["word_count"])
            for case in self.cases
            if case["expected_language"] == "ug"
        )
        expected = Counter(
            {
                (alphabet, length): CASES_PER_BUCKET
                for alphabet in {
                    "Uyghur Arabic (UEY)",
                    "Uyghur Latin (ULY)",
                    "Uyghur Cyrillic (UKY)",
                    "Uyghur New Script (UYY)",
                }
                for length in LENGTHS
            }
        )
        self.assertEqual(uighur_alphabets, expected)

        for case in self.cases:
            if case["expected_language"] != "ug":
                continue
            with self.subTest(case=case["id"]):
                letters = [
                    character
                    for character in case["text"]
                    if character.isalpha()
                ]
                expected_name = {
                    "Arab": "ARABIC",
                    "Cyrl": "CYRILLIC",
                    "Latn": "LATIN",
                }[case["script"]]
                matching = [
                    character
                    for character in letters
                    if expected_name in unicodedata.name(character, "")
                ]
                self.assertGreater(len(matching) / len(letters), 0.95)

    def test_cyrillic_uzbek_contains_cyrillic_letters(self) -> None:
        for case in self.cases:
            if case["expected_language"] == "uz" and case["script"] == "Cyrl":
                with self.subTest(case=case["id"]):
                    letters = [character for character in case["text"] if character.isalpha()]
                    cyrillic = [
                        character
                        for character in letters
                        if "CYRILLIC" in unicodedata.name(character, "")
                    ]
                    self.assertGreater(len(cyrillic) / len(letters), 0.95)

    def test_northern_pashto_does_not_overlap_training_prefix_or_itself(self) -> None:
        ranges = sorted(
            (
                case["source"]["token_start"],
                case["source"]["token_end"],
            )
            for case in self.cases
            if case["id"].startswith("ps-pbu-")
        )
        self.assertTrue(ranges)
        self.assertGreaterEqual(ranges[0][0], 1_001)
        for previous, current in zip(ranges, ranges[1:]):
            self.assertLess(previous[1], current[0])

    def test_regional_udhr_cases_do_not_overlap_training_or_each_other(self) -> None:
        for prefix in {"az-cyrl-", "ku-kmr-", "pa-pnb-", "tk-cyrl-"}:
            ranges = sorted(
                (case["source"]["token_start"], case["source"]["token_end"])
                for case in self.cases
                if case["id"].startswith(prefix)
            )
            with self.subTest(prefix=prefix):
                self.assertTrue(ranges)
                self.assertGreaterEqual(ranges[0][0], 1_001)
                for previous, current in zip(ranges, ranges[1:]):
                    self.assertLess(previous[1], current[0])

    def test_new_script_cases_use_the_declared_unicode_script(self) -> None:
        script_names = {
            "Armn": "ARMENIAN",
            "Beng": "BENGALI",
            "Deva": "DEVANAGARI",
            "Geor": "GEORGIAN",
            "Hebr": "HEBREW",
            "Telu": "TELUGU",
        }
        minimum_shares = {
            "Armn": 0.90,
            "Beng": 0.70,
            "Deva": 0.70,
            "Geor": 0.90,
            "Hebr": 0.90,
            "Telu": 0.70,
        }
        for case in self.cases:
            if case["script"] not in script_names:
                continue
            with self.subTest(case=case["id"]):
                letters = [character for character in case["text"] if character.isalpha()]
                matching = [
                    character
                    for character in letters
                    if script_names[case["script"]] in unicodedata.name(character, "")
                ]
                self.assertGreaterEqual(
                    len(matching) / len(letters), minimum_shares[case["script"]]
                )

    def test_east_asian_cases_use_the_declared_writing_system(self) -> None:
        for case in self.cases:
            if case["script"] not in {"Hani", "Jpan"}:
                continue
            with self.subTest(case=case["id"]):
                names = [
                    unicodedata.name(character, "")
                    for character in case["text"]
                    if character.isalpha()
                ]
                if case["script"] == "Hani":
                    matching = [name for name in names if "CJK" in name]
                else:
                    matching = [
                        name
                        for name in names
                        if "CJK" in name
                        or "HIRAGANA" in name
                        or "KATAKANA" in name
                    ]
                self.assertGreaterEqual(len(matching) / len(names), 0.70)

    def test_ids_and_texts_are_unique(self) -> None:
        ids = [case["id"] for case in self.cases]
        texts = [
            (
                case["expected_language"],
                case["script"],
                case.get("alphabet"),
                case.get("variety"),
                case["text"],
            )
            for case in self.cases
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(texts), len(set(texts)))

    def test_declared_word_counts_are_exact(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(len(case["text"].split()), case["word_count"])

    def test_text_is_valid_and_nonempty(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertNotIn("\ufffd", case["text"])
                self.assertTrue(any(character.isalpha() for character in case["text"]))
                self.assertIn(
                    case["source"]["dataset"],
                    {"FLORES-200", "NaijaSynCor", "Tatoeba", "UDHR"},
                )
                if case["source"]["dataset"] == "FLORES-200":
                    self.assertEqual(case["source"]["split"], "devtest")
                elif case["source"]["dataset"] == "NaijaSynCor":
                    self.assertEqual(case["source"]["split"], "test")
                elif case["source"]["dataset"] == "UDHR":
                    self.assertEqual(
                        case["source"]["split"], "heldout_after_training_prefix"
                    )
                else:
                    self.assertEqual(
                        case["source"]["split"], "per_language_export"
                    )


if __name__ == "__main__":
    unittest.main()
