from __future__ import annotations

import unittest

from tools.uyghur_transliteration import (
    arabic_to_cyrillic,
    arabic_to_latin,
    arabic_to_new_script,
)


class UyghurTransliterationTests(unittest.TestCase):
    def test_complete_core_alphabet_mappings(self) -> None:
        arabic = "ا ە ب پ ت ج چ خ د ر ز ژ س ش غ ف ق ك گ ڭ ل م ن ھ و ۇ ۆ ئۈ ۋ ې ى ي"
        self.assertEqual(
            arabic_to_latin(arabic),
            "a e b p t j ch x d r z zh s sh gh f q k g ng l m n h o u ö ü w ë i y",
        )
        self.assertEqual(
            arabic_to_cyrillic(arabic),
            "а ә б п т җ ч х д р з ж с ш ғ ф қ к г ң л м н һ о у ө ү в е и й",
        )
        self.assertEqual(
            arabic_to_new_script(arabic),
            "a ə b p t j q h d r z ⱬ s x ƣ f ⱪ k g ng l m n ⱨ o u ɵ ü w e i y",
        )

    def test_cyrillic_iotated_vowels(self) -> None:
        self.assertEqual(arabic_to_cyrillic("يا يۇ يو"), "я ю ё")

    def test_conversion_preserves_whitespace_token_count(self) -> None:
        source = "ھەر بىر ئىنسان ئەركىن ۋە باراۋەر تۇغۇلىدۇ"
        for converter in (arabic_to_latin, arabic_to_cyrillic, arabic_to_new_script):
            with self.subTest(converter=converter.__name__):
                self.assertEqual(
                    len(converter(source).split()),
                    len(source.split()),
                )


if __name__ == "__main__":
    unittest.main()
