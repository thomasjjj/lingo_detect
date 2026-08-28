from __future__ import annotations

import unittest

from tools.evaluate_detector import evaluate, language_code, parse_prediction


class ResultObject:
    language_code = "uk"


class EvaluatorTests(unittest.TestCase):
    def test_supported_detector_result_shapes(self) -> None:
        self.assertEqual(language_code("en"), "en")
        self.assertEqual(language_code({"language_code": "ar"}), "ar")
        self.assertEqual(language_code(("ru", 0.9)), "ru")
        self.assertEqual(language_code(ResultObject()), "uk")

    def test_script_only_fallback(self) -> None:
        self.assertEqual(
            parse_prediction({"language_code": None, "script": "Cyrillic"}),
            {"language_code": None, "script": "Cyrl"},
        )
        self.assertEqual(
            parse_prediction("Latin"),
            {"language_code": None, "script": "Latn"},
        )

    def test_evaluate_marks_predictions(self) -> None:
        cases = [
            {"text": "hello", "expected_language": "en", "script": "Latn"}
        ]
        result = evaluate(cases, lambda text: "en")
        self.assertEqual(result["rows"][0]["resolution"], "language")

    def test_evaluate_marks_useful_script_fallback(self) -> None:
        cases = [{"text": "ва", "expected_language": "tg", "script": "Cyrl"}]
        result = evaluate(
            cases,
            lambda text: {"language_code": None, "script": "Cyrl"},
        )
        self.assertEqual(result["rows"][0]["resolution"], "script")


if __name__ == "__main__":
    unittest.main()
