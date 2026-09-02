from __future__ import annotations

import unittest

from lingo_detect import DetectionResult, detect


class DetectorTests(unittest.TestCase):
    def test_no_letters_returns_no_resolution(self) -> None:
        result = detect("123 — !!!")
        self.assertIsNone(result.script)
        self.assertIsNone(result.language_code)
        self.assertEqual(result.resolution, "none")

    def test_distinctive_letters_can_resolve_one_character(self) -> None:
        self.assertEqual(detect("ї").language_code, "uk")
        self.assertEqual(detect("ښ").language_code, "ps")
        self.assertEqual(detect("ڭ").language_code, "ug")

    def test_ambiguous_character_falls_back_to_script(self) -> None:
        cyrillic = detect("а")
        arabic = detect("و")
        self.assertEqual((cyrillic.script, cyrillic.language_code), ("Cyrl", None))
        self.assertEqual((arabic.script, arabic.language_code), ("Arab", None))
        turkic = detect("ğ")
        self.assertEqual((turkic.script, turkic.language_code), ("Latn", None))
        urdu_punjabi = detect("ٹ")
        self.assertEqual(
            (urdu_punjabi.script, urdu_punjabi.language_code), ("Arab", None)
        )

    def test_both_uzbek_scripts_map_to_uz(self) -> None:
        self.assertEqual(detect("oʻzbekiston respublikasi").language_code, "uz")
        self.assertEqual(detect("ҳар бир инсон ҳуқуқига эгадир").language_code, "uz")

    def test_persian_is_detected(self) -> None:
        result = detect("این یک متن فارسی برای آزمایش تشخیص زبان است")
        self.assertEqual((result.script, result.language_code), ("Arab", "fa"))
        self.assertEqual(result.label, "Arabic · Persian (Farsi)")

    def test_turkish_is_detected_with_dotted_capital_i(self) -> None:
        result = detect("İnsan hakları herkes için önemlidir")
        self.assertEqual((result.script, result.language_code), ("Latn", "tr"))
        self.assertEqual(result.label, "Latin · Turkish")
        self.assertEqual(detect("İLE").language_code, "tr")

    def test_regional_expansion_languages(self) -> None:
        samples = {
            "az": "Bəşər ailəsinin bütün üzvlərinin bərabər və ayrılmaz hüquqları vardır",
            "he": "כל אדם זכאי לכל הזכויות והחירויות",
            "hy": "Յուրաքանչյուր ոք ունի բոլոր իրավունքներն ու ազատությունները",
            "ka": "ყოველ ადამიანს აქვს ყველა უფლება და თავისუფლება",
            "kk": "Әр адам құқықтары мен бостандықтарына ие",
            "ku": "هەموو مرۆڤێک مافی ژیان و ئازادی هەیە",
            "ky": "Ар бир адам укуктарга жана эркиндиктерге ээ",
            "pa": "ہر شخص نوں آزادی تے برابر حقوق دا حق اے",
            "sd": "هر هڪ ماڻهو کي حق ۽ آزادي حاصل آهي",
            "tk": "Her bir adam hukuklara we azatlyklara haklydyr",
            "yi": "היות װי יעדער מענטש האָט אַ רעכט אױף פֿרײַהײט",
        }
        for language_code, text in samples.items():
            with self.subTest(language_code=language_code):
                self.assertEqual(detect(text).language_code, language_code)

    def test_global_expansion_languages(self) -> None:
        samples = {
            "bn": "সকল মানুষ স্বাধীনভাবে সমান মর্যাদা এবং অধিকার নিয়ে জন্মগ্রহণ করে",
            "de": "Alle Menschen sind frei und gleich an Würde und Rechten geboren",
            "es": "Todos los seres humanos nacen libres e iguales en dignidad y derechos",
            "fr": "Tous les êtres humains naissent libres et égaux en dignité et en droits",
            "ha": "An haifi dukkan mutane da 'yanci kuma suna da mutunci da hakkoki",
            "hi": "सभी मनुष्य स्वतंत्र और सम्मान तथा अधिकारों में समान जन्म लेते हैं",
            "id": "Semua manusia dilahirkan bebas dan mempunyai martabat dan hak yang sama",
            "ja": "すべての人間は、生まれながらにして自由であり、尊厳と権利について平等です",
            "mr": "सर्व मानव स्वतंत्र जन्माला आले असून त्यांना समान प्रतिष्ठा आणि अधिकार आहेत",
            "pcm": "How you dey now? I dey fine and we thank God",
            "pt": "Todos os seres humanos nascem livres e iguais em dignidade e direitos",
            "sw": "Watu wote wamezaliwa huru na wana hadhi na haki sawa",
            "te": "మానవులందరూ స్వేచ్ఛగా సమాన గౌరవం మరియు హక్కులతో జన్మించారు",
            "vi": "Mọi người sinh ra đều được tự do và bình đẳng về nhân phẩm và quyền",
            "zh": "人人生而自由，在尊严和权利上一律平等",
        }
        for language_code, text in samples.items():
            with self.subTest(language_code=language_code):
                self.assertEqual(detect(text).language_code, language_code)

    def test_chinese_and_japanese_writing_systems_are_distinguished(self) -> None:
        chinese = detect("这是一个用于测试语言检测的中文句子")
        japanese = detect("これは言語検出をテストするための日本語の文です")
        self.assertEqual((chinese.script, chinese.language_code), ("Hani", "zh"))
        self.assertEqual((japanese.script, japanese.language_code), ("Jpan", "ja"))

    def test_uighur_alphabets_map_to_ug(self) -> None:
        samples = {
            "Arab": "ھەر بىر ئىنسان ئەركىن تۇغۇلىدۇ",
            "Latn": "hemme adem behrimen bolushqa hoquqluq herqandaq ademni",
            "Cyrl": "һәммә адәм бәһримән болушқа һоқуқлуқ һәрқандақ адәмни",
            "Latn-UYY": "ⱨər bir insan ərkin tuƣulidu",
        }
        for alphabet, text in samples.items():
            with self.subTest(alphabet=alphabet):
                self.assertEqual(detect(text).language_code, "ug")

    def test_mixed_latin_acronym_does_not_hide_native_script(self) -> None:
        result = detect("GMT کې د")
        self.assertEqual(result.script, "Arab")
        self.assertIsNone(result.language_code)

    def test_result_is_structured_and_serialisable(self) -> None:
        result = detect("the right to freedom")
        self.assertIsInstance(result, DetectionResult)
        value = result.as_dict()
        self.assertEqual(value["script"], "Latn")
        self.assertEqual(value["language_code"], "en")
        self.assertEqual(value["label"], "Latin · English")
        self.assertTrue(value["alternatives"])
        self.assertAlmostEqual(
            sum(alternative["score"] for alternative in value["alternatives"]),
            1.0,
            places=5,
        )

    def test_long_string_is_supported(self) -> None:
        result = detect(("This is a long English sentence. " * 1_000).strip())
        self.assertEqual(result.language_code, "en")

    def test_non_string_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            detect(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
