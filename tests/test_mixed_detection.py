from __future__ import annotations

import json
import unittest

from lingo_detect import DetectionSegment, MixedDetectionResult, detect, detect_mixed


class MixedDetectionTests(unittest.TestCase):
    def test_english_around_russian_span(self) -> None:
        text = (
            "The museum is called Государственный Эрмитаж расположен в Санкт-Петербурге, "
            "and it is located in Saint Petersburg."
        )
        result = detect_mixed(text)

        self.assertIsInstance(result, MixedDetectionResult)
        self.assertEqual(result.primary, detect(text))
        self.assertEqual(result.scripts, ("Latn", "Cyrl"))
        self.assertEqual(result.language_codes, ("en", "ru"))
        self.assertTrue(result.is_mixed_script)
        self.assertTrue(result.is_mixed_language)
        self.assertTrue(result.is_mixed)
        self.assertFalse(result.has_unresolved_segments)
        self.assertEqual(
            [(segment.script, segment.language_code) for segment in result.segments],
            [("Latn", "en"), ("Cyrl", "ru"), ("Latn", "en")],
        )
        self.assertEqual("".join(segment.text for segment in result.segments), text)
        for segment in result.segments:
            self.assertIsInstance(segment, DetectionSegment)
            self.assertEqual(text[segment.start : segment.end], segment.text)

    def test_english_around_persian_span(self) -> None:
        text = (
            "The Persian statement حقوق بشر در این کشور بسیار مهم است means that "
            "human rights are very important here, "
            "and this explanation is English."
        )
        result = detect_mixed(text)

        self.assertEqual(result.scripts, ("Latn", "Arab"))
        self.assertEqual(result.language_codes, ("en", "fa"))
        self.assertEqual(
            [(segment.script, segment.language_code) for segment in result.segments],
            [("Latn", "en"), ("Arab", "fa"), ("Latn", "en")],
        )
        self.assertEqual("".join(segment.text for segment in result.segments), text)

    def test_short_wikipedia_name_preserves_script_fallback(self) -> None:
        text = "Moscow (Russian: Москва) is the capital of Russia."
        result = detect_mixed(text)
        cyrillic = next(segment for segment in result.segments if segment.script == "Cyrl")

        self.assertTrue(result.is_mixed_script)
        self.assertTrue(result.has_unresolved_segments)
        self.assertIsNone(cyrillic.language_code)
        self.assertEqual(cyrillic.resolution, "script")
        self.assertEqual(cyrillic.detection.alternatives[0].language_code, "ru")

    def test_same_script_languages_split_at_sentence_boundary(self) -> None:
        text = (
            "This is an English sentence. "
            "Oʻzbekiston respublikasi mustaqil davlat."
        )
        result = detect_mixed(text)

        self.assertEqual(result.scripts, ("Latn",))
        self.assertEqual(result.language_codes, ("en", "uz"))
        self.assertFalse(result.is_mixed_script)
        self.assertTrue(result.is_mixed_language)
        self.assertTrue(result.is_mixed)
        self.assertEqual(len(result.segments), 2)

    def test_same_language_sentences_merge_again(self) -> None:
        text = "This is the first sentence. This is the second sentence."
        result = detect_mixed(text)

        self.assertFalse(result.is_mixed)
        self.assertEqual(result.language_codes, ("en",))
        self.assertEqual(len(result.segments), 1)
        self.assertEqual(result.segments[0].text, text)

    def test_no_letter_and_empty_inputs(self) -> None:
        no_letters = detect_mixed("123 — !!!")
        self.assertEqual(len(no_letters.segments), 1)
        self.assertEqual(no_letters.segments[0].resolution, "none")
        self.assertEqual(no_letters.scripts, ())
        self.assertTrue(no_letters.has_unresolved_segments)

        empty = detect_mixed("")
        self.assertEqual(empty.segments, ())
        self.assertEqual(empty.primary.resolution, "none")
        self.assertFalse(empty.has_unresolved_segments)

    def test_result_is_json_serialisable(self) -> None:
        value = detect_mixed("English and Русский текст.").as_dict()
        json.dumps(value, ensure_ascii=False)
        self.assertIn("primary", value)
        self.assertIn("segments", value)
        self.assertIn("is_mixed", value)

    def test_non_string_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            detect_mixed(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
