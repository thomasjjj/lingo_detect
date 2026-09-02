from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files


CLAUSE_BOUNDARY_PATTERN = re.compile(
    r"(?:\r\n|\r|\n|[.!?;:]+)[\t \f\v]*",
    re.UNICODE,
)
APOSTROPHES = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'"})
SCRIPT_NAMES = {
    "Arab": "Arabic",
    "Armn": "Armenian",
    "Beng": "Bengali",
    "Cyrl": "Cyrillic",
    "Deva": "Devanagari",
    "Geor": "Georgian",
    "Hani": "Han",
    "Hebr": "Hebrew",
    "Jpan": "Japanese",
    "Latn": "Latin",
    "Telu": "Telugu",
}
LANGUAGE_NAMES = {
    "ar": "Arabic",
    "az": "Azerbaijani",
    "bn": "Bengali",
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fa": "Persian (Farsi)",
    "fr": "French",
    "ha": "Hausa",
    "he": "Hebrew",
    "hi": "Hindi",
    "hy": "Armenian",
    "id": "Indonesian",
    "ja": "Japanese",
    "ka": "Georgian",
    "kk": "Kazakh",
    "ku": "Kurdish",
    "ky": "Kyrgyz",
    "mr": "Marathi",
    "pa": "Punjabi",
    "pcm": "Nigerian Pidgin",
    "pt": "Portuguese",
    "ps": "Pashto",
    "ru": "Russian",
    "sd": "Sindhi",
    "sw": "Swahili",
    "te": "Telugu",
    "tg": "Tajik",
    "tk": "Turkmen",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "ug": "Uyghur",
    "uz": "Uzbek",
    "vi": "Vietnamese",
    "yi": "Yiddish",
    "zh": "Mandarin Chinese",
}

CUE_WORDS = {
    "ar": {
        "في", "من", "أن", "على", "إلى", "أو", "لا", "هو", "هي", "هذا",
        "هذه", "الذي", "التي", "كل", "لكل", "كان", "بين", "دون",
    },
    "az": {
        "və", "bir", "hər", "hüququ", "malikdir", "ya", "heç", "bu", "ilə",
        "üçün", "öz", "olan", "deyil",
        "вә", "бир", "һәр", "һүгугуна", "маликдир", "ја", "һеч", "бу", "илә",
        "үчүн", "өз", "олан",
        "و", "کی", "ایله", "اوچون", "بیر", "او", "بو", "وار", "سونرا", "گؤره",
    },
    "bn": {
        "এবং", "ও", "এর", "এই", "একটি", "যে", "না", "জন্য", "থেকে", "হয়",
        "করে", "সঙ্গে", "মানুষ", "সব", "কোনো",
    },
    "de": {
        "der", "die", "das", "und", "in", "von", "zu", "den", "mit", "für",
        "ist", "auf", "nicht", "ein", "eine", "als", "auch", "werden",
    },
    "en": {
        "the", "of", "and", "to", "in", "or", "is", "are", "that", "this",
        "with", "for", "from", "shall", "has", "have", "not", "every", "all",
    },
    "es": {
        "de", "la", "que", "el", "en", "y", "a", "los", "se", "del", "las",
        "por", "un", "para", "con", "no", "una", "su", "al",
    },
    "fa": {
        "از", "آن", "این", "است", "با", "برای", "به", "بود", "در", "را",
        "که", "و", "هر", "همه", "هیچ", "یک", "خود", "شود", "دارد", "نیز",
    },
    "fr": {
        "de", "la", "le", "les", "des", "et", "à", "en", "un", "une", "du",
        "que", "est", "pour", "dans", "pas", "sur", "ce", "qui",
    },
    "ha": {
        "da", "na", "ne", "ni", "a", "cikin", "wani", "wannan", "ba", "ko",
        "ya", "ta", "su", "don", "kuma", "daga", "zuwa",
    },
    "he": {
        "של", "כל", "אדם", "או", "על", "את", "לא", "הוא", "היא", "זכאי",
        "החוק", "עם", "אם", "זה",
    },
    "hi": {
        "और", "के", "का", "में", "से", "को", "है", "हैं", "एक", "यह",
        "कि", "पर", "नहीं", "लिए", "भी", "कर", "हो",
    },
    "hy": {
        "ու", "ոք", "իրավունք", "ունի", "եւ", "կամ", "է", "իր", "յուրաքանչյուր",
        "այս", "ամեն", "ոչ", "չի", "են",
    },
    "id": {
        "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "ini",
        "itu", "tidak", "adalah", "sebagai", "atau", "oleh", "dalam",
    },
    "ja": set(),
    "ka": {
        "და", "უფლება", "აქვს", "ადამიანს", "ყველა", "ყოველ", "ან", "უნდა",
        "არ", "მისი", "თუ", "ამ",
    },
    "kk": {
        "және", "адам", "әр", "мен", "немесе", "құқығы", "бар", "өз", "арқылы",
        "тиіс", "тең", "осы", "ешкім",
    },
    "ku": {
        "لە", "و", "بە", "کە", "بۆ", "ئەو", "سەر", "دا", "بوو", "نییە",
        "û", "ku", "bi", "ji", "di", "li", "xwe", "hemû", "maf", "herkes",
        "kirin", "heye",
    },
    "ky": {
        "жана", "менен", "адам", "бир", "ар", "же", "укуктуу", "тийиш", "бардык",
        "өз", "эмес", "ээ", "эч", "үчүн",
    },
    "mr": {
        "आणि", "आहे", "आहेत", "मध्ये", "नाही", "यांच्या", "तसे", "मात्र",
        "करून", "म्हणून", "होती", "होते",
    },
    "pa": {
        "تے", "اے", "دا", "دی", "دے", "وچ", "ہر", "شخص", "توں", "یا", "کسے",
        "نوں", "کوئی", "اوہدے", "وی",
    },
    "pcm": {
        "dey", "di", "na", "wey", "dem", "don", "wetin", "sey", "sef", "con",
    },
    "pt": {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é",
        "com", "não", "uma", "os", "no", "se", "na", "por",
    },
    "ps": {
        "د", "په", "او", "چې", "له", "څوک", "شي", "وي", "نه", "هغه", "سره",
        "يا", "لري", "هر", "کښې", "کې", "يو", "یو", "دي", "ده",
    },
    "ru": {
        "и", "в", "во", "на", "не", "или", "что", "это", "как", "по", "из",
        "к", "с", "для", "он", "она", "имеет", "каждый", "человек", "никто",
    },
    "sd": {
        "جي", "هڪ", "کي", "جو", "کان", "آهي", "لاء", "سان", "تي", "ڪئي",
        "ڪرڻ", "جيڪو", "ڪندي", "ٿي", "هو",
    },
    "sw": {
        "na", "ya", "wa", "kwa", "katika", "ni", "kuwa", "au", "hii", "haki",
        "kila", "watu", "mtu", "si", "la", "za", "kutoka",
    },
    "te": {
        "మరియు", "యొక్క", "లో", "ఒక", "ఈ", "కు", "నుండి", "కోసం", "అని", "ఉంది",
        "కాదు", "వారు", "అన్ని", "లేదా",
    },
    "tg": {
        "ва", "дар", "ба", "ки", "ҳар", "як", "ё", "бо", "дорад", "аз",
        "инсон", "ҳақ", "ин", "шавад", "онҳо", "нест", "барои",
    },
    "tk": {
        "we", "bir", "adam", "her", "öz", "haklydyr", "ýa", "hem", "bu", "hiç",
        "deň", "üçin", "bilen",
        "ве", "бир", "адам", "хер", "өз", "хаклыдыр", "я", "хем", "бу", "хич",
        "дең", "үчин", "билен",
    },
    "tr": {
        "ve", "için", "ile", "olarak", "olan", "olduğu", "hak", "veya", "de",
        "da", "kendi", "hiç", "karşı", "daha", "çok", "tarafından",
    },
    "uk": {
        "і", "й", "та", "в", "у", "на", "не", "або", "що", "це", "як", "до",
        "з", "для", "він", "вона", "має", "кожна", "людина", "ніхто", "від",
    },
    "ur": {
        "کے", "کی", "کا", "اور", "میں", "سے", "کو", "ہے", "ہیں", "اس", "یا",
        "پر", "ہر", "نہیں", "جائے", "ایک", "کہ", "جو", "کوئی",
    },
    "ug": {
        "ۋە", "بىر", "ھەر", "ئىنسان", "ياكى", "بىلەن", "ئۇ", "بۇ", "ئۈچۈن",
        "بار", "ئەمەس", "ئۆز", "ھوقۇق", "قىلىش", "بولغان",
        "we", "bir", "her", "insan", "yaki", "bilen", "u", "bu", "üchün",
        "bar", "emes", "öz", "hoquq", "qilish", "bolghan",
        "вә", "һәр", "инсан", "яки", "билән", "үчүн", "әмәс", "өз",
        "һуқуқ", "қилиш", "болған",
        "wə", "ⱨər", "bilən", "üqün", "əməs", "ɵz", "ⱨoⱪuⱪ", "ⱪilix",
        "bolƣan",
    },
    "uz": {
        "va", "bir", "inson", "yoki", "har", "bilan", "egadir", "o'z", "mumkin",
        "barcha", "bo'lgan", "hech", "emas", "kim", "uchun", "bu", "ham",
        "o'zbekiston", "respublikasi",
        "ва", "бир", "инсон", "ёки", "ҳар", "билан", "эгадир", "ўз", "мумкин",
        "барча", "бўлган", "ҳеч", "эмас", "ким", "учун", "бу", "ҳам",
    },
    "vi": {
        "và", "của", "là", "có", "trong", "một", "được", "không", "cho", "với",
        "các", "những", "người", "này", "từ", "đến", "để",
    },
    "yi": {
        "און", "די", "דער", "אױף", "ניט", "זײ", "איז", "אין", "פֿון", "מיט",
        "צו", "דאָס",
    },
    "zh": set(),
}
CUE_LANGUAGE_COUNTS = Counter(
    word for language_words in CUE_WORDS.values() for word in language_words
)
UNIQUE_CUE_WORDS = {
    language: {
        word for word in language_words if CUE_LANGUAGE_COUNTS[word] == 1
    }
    for language, language_words in CUE_WORDS.items()
}

# Weights are deliberately asymmetric: letters confined to one supported
# orthography carry more evidence than letters shared by related languages.
DISTINCTIVE_CHARACTERS = {
    "ar": {"ة": 2.3} | {character: 0.4 for character in "أإ"} | {"آ": 0.3},
    "az": {character: 3.2 for character in "јҹҝ"} | {"ə": 0.15},
    "bn": {},
    "de": {"ß": 3.0},
    "en": {"w": 1.1},
    "es": {"ñ": 3.0},
    "fa": {"ۀ": 3.0},
    "fr": {"œ": 3.0},
    "ha": {character: 3.2 for character in "ɓɗƙ"},
    "he": {},
    "hi": {},
    "hy": {},
    "id": {},
    "ja": {},
    "ka": {},
    "kk": {"ұ": 3.2, "і": 0.5}
    | {character: 0.35 for character in "қғәңөү"},
    "ku": {character: 3.2 for character in "ێڕڵڤêîû"} | {"ۆ": 0.35},
    "ky": {character: 0.35 for character in "ңөү"},
    "mr": {"ळ": 3.2},
    "pa": {},
    "pcm": {},
    "pt": {character: 3.0 for character in "ãõ"},
    "ps": {character: 3.2 for character in "ټځڅډړږښګڼېۍ"}
    | {character: 0.5 for character in "پچژ"},
    "ru": {"щ": 0.5, "ъ": 0.3},
    "sd": {character: 3.2 for character in "ڪٽڊڻٿڏڳڙٻڀڌڇڃٺڄڍ"},
    "sw": {},
    "te": {},
    "tg": {character: 3.0 for character in "ӣҷӯ"}
    | {character: 0.7 for character in "ғқҳ"},
    "tk": {character: 3.2 for character in "ýňäž"},
    "tr": {},
    "uk": {character: 3.2 for character in "їєґ"},
    "ur": {},
    "ug": {character: 3.2 for character in "ڭۇۈۋ"}
    | {character: 4.0 for character in "ƣɵⱨⱪⱬ"}
    | {character: 2.2 for character in "ëé"},
    "uz": {"ў": 6.0, "ʻ": 3.0, "ʼ": 3.0}
    | {character: 0.65 for character in "қғҳ"}
    | {"q": 0.45, "x": 0.35},
    "vi": {character: 3.2 for character in "ăđơư"},
    "yi": {character: 3.5 for character in "װױײ"},
    "zh": {},
}


@dataclass(frozen=True, slots=True)
class LanguageScore:
    language_code: str
    score: float


@dataclass(frozen=True, slots=True)
class DetectionResult:
    script: str | None
    language_code: str | None
    confidence: float
    alternatives: tuple[LanguageScore, ...]

    @property
    def resolution(self) -> str:
        if self.language_code is not None:
            return "language"
        if self.script is not None:
            return "script"
        return "none"

    @property
    def label(self) -> str:
        if self.script is None:
            return "Unknown script · uncertain"
        script_name = SCRIPT_NAMES[self.script]
        if self.language_code is None:
            return f"{script_name} · uncertain"
        return f"{script_name} · {LANGUAGE_NAMES[self.language_code]}"

    def as_dict(self) -> dict:
        result = asdict(self)
        result["resolution"] = self.resolution
        result["label"] = self.label
        return result


@dataclass(frozen=True, slots=True)
class DetectionSegment:
    """A contiguous text span and its independent detection result."""

    start: int
    end: int
    text: str
    detection: DetectionResult

    @property
    def script(self) -> str | None:
        return self.detection.script

    @property
    def language_code(self) -> str | None:
        return self.detection.language_code

    @property
    def confidence(self) -> float:
        return self.detection.confidence

    @property
    def resolution(self) -> str:
        return self.detection.resolution

    @property
    def label(self) -> str:
        return self.detection.label

    def as_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            **self.detection.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class MixedDetectionResult:
    """Whole-text detection plus ordered language/script-aware spans."""

    primary: DetectionResult
    segments: tuple[DetectionSegment, ...]

    @staticmethod
    def _ordered_unique(values: tuple[str | None, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(value for value in values if value is not None))

    @property
    def scripts(self) -> tuple[str, ...]:
        return self._ordered_unique(tuple(segment.script for segment in self.segments))

    @property
    def language_codes(self) -> tuple[str, ...]:
        return self._ordered_unique(
            tuple(segment.language_code for segment in self.segments)
        )

    @property
    def is_mixed_script(self) -> bool:
        return len(self.scripts) > 1

    @property
    def is_mixed_language(self) -> bool:
        return len(self.language_codes) > 1

    @property
    def is_mixed(self) -> bool:
        return self.is_mixed_script or self.is_mixed_language

    @property
    def has_unresolved_segments(self) -> bool:
        return any(segment.language_code is None for segment in self.segments)

    def as_dict(self) -> dict:
        return {
            "primary": self.primary.as_dict(),
            "segments": tuple(segment.as_dict() for segment in self.segments),
            "scripts": self.scripts,
            "language_codes": self.language_codes,
            "is_mixed_script": self.is_mixed_script,
            "is_mixed_language": self.is_mixed_language,
            "is_mixed": self.is_mixed,
            "has_unresolved_segments": self.has_unresolved_segments,
        }


def _script_of(character: str) -> str | None:
    name = unicodedata.name(character, "")
    if "ARABIC" in name:
        return "Arab"
    if "ARMENIAN" in name:
        return "Armn"
    if "BENGALI" in name:
        return "Beng"
    if "CYRILLIC" in name:
        return "Cyrl"
    if "DEVANAGARI" in name:
        return "Deva"
    if "GEORGIAN" in name:
        return "Geor"
    if "HEBREW" in name:
        return "Hebr"
    if "HIRAGANA" in name or "KATAKANA" in name:
        return "Jpan"
    if "LATIN" in name:
        return "Latn"
    if "TELUGU" in name:
        return "Telu"
    if "CJK UNIFIED IDEOGRAPH" in name or "CJK COMPATIBILITY IDEOGRAPH" in name:
        return "Hani"
    return None


def _script_characters(text: str) -> list[tuple[int, str]]:
    """Return context-aware script classifications for recognized letters.

    Han ideographs are shared by Chinese and Japanese. If Japanese kana occur
    in the same text, treat the ideographs as part of the Japanese writing
    system so they do not overwhelm or fragment the Japanese signal.
    """
    classified = [
        (index, script)
        for index, character in enumerate(text)
        if character.isalpha() and (script := _script_of(character)) is not None
    ]
    if any(script == "Jpan" for _, script in classified):
        return [
            (index, "Jpan" if script == "Hani" else script)
            for index, script in classified
        ]
    return classified


def _normalise(text: str) -> str:
    # Unicode case-folding represents Turkish capital dotted İ as i + U+0307.
    # Collapse that sequence so the combining dot does not split the word.
    return unicodedata.normalize("NFKC", text).casefold().replace("i\u0307", "i")


def _tokens(text: str) -> list[str]:
    translated = text.translate(APOSTROPHES)
    tokens: list[str] = []
    current: list[str] = []
    for index, character in enumerate(translated):
        is_letter_or_mark = character.isalpha() or unicodedata.category(
            character
        ).startswith("M")
        apostrophe_inside_word = (
            character == "'"
            and bool(current)
            and index + 1 < len(translated)
            and (
                translated[index + 1].isalpha()
                or unicodedata.category(translated[index + 1]).startswith("M")
            )
        )
        if is_letter_or_mark or apostrophe_inside_word:
            current.append(character)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens


def _ngrams(words: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for word in words:
        padded = f"^{word}$"
        for size in (2, 3, 4):
            counts.update(
                padded[index : index + size]
                for index in range(len(padded) - size + 1)
            )
    return counts


@lru_cache(maxsize=1)
def _load_profiles() -> dict:
    resource = files("lingo_detect").joinpath("profiles.json")
    return json.loads(resource.read_text(encoding="utf-8"))["profiles"]


def _rank_distance(input_counts: Counter[str], profile_ngrams: list[str]) -> float:
    input_ranked = [item for item, _ in input_counts.most_common(300)]
    if not input_ranked:
        return 1.0
    profile_ranks = {item: rank for rank, item in enumerate(profile_ngrams)}
    missing_rank = len(profile_ngrams)
    distance = sum(
        abs(input_rank - profile_ranks.get(item, missing_rank))
        for input_rank, item in enumerate(input_ranked)
    )
    return distance / (len(input_ranked) * missing_rank)


def _softmax(raw_scores: dict[str, float]) -> list[LanguageScore]:
    maximum = max(raw_scores.values())
    exponentials = {
        language: math.exp(min(50.0, score - maximum))
        for language, score in raw_scores.items()
    }
    total = sum(exponentials.values())
    return [
        LanguageScore(language, round(value / total, 6))
        for language, value in sorted(
            exponentials.items(), key=lambda item: item[1], reverse=True
        )
    ]


def _language_is_resolved(
    alternatives: list[LanguageScore],
    word_count: int,
    letter_count: int,
    script_confidence: float,
    distinctive_score: float,
    cue_score: float,
) -> bool:
    if script_confidence < 0.70:
        return False
    top = alternatives[0].score
    second = alternatives[1].score if len(alternatives) > 1 else 0.0
    margin = top - second
    if letter_count <= 2:
        return (distinctive_score >= 2.5 and top >= 0.80) or (
            cue_score >= 0.9 and top >= 0.85
        )
    if word_count <= 1:
        return (top >= 0.93 and margin >= 0.60) or (
            distinctive_score >= 1.0 and top >= 0.55
        ) or (cue_score >= 0.9 and top >= 0.70)
    if word_count <= 3:
        return top >= 0.66 and margin >= 0.20
    if word_count >= 1_000:
        return top >= 0.20 and margin >= 0.10
    return top >= 0.30 and margin >= 0.05


def detect(text: str) -> DetectionResult:
    """Detect the highest defensible script/language resolution for ``text``."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalised = _normalise(text)
    script_counts = Counter(script for _, script in _script_characters(normalised))
    if not script_counts:
        return DetectionResult(None, None, 0.0, ())

    # A short Latin acronym embedded in Arabic/Cyrillic text can tie the native
    # script. In a tie, prefer the non-Latin script instead of the acronym.
    script = max(
        script_counts,
        key=lambda candidate: (script_counts[candidate], candidate != "Latn"),
    )
    script_letters = script_counts[script]
    total_script_letters = sum(script_counts.values())
    script_confidence = script_letters / total_script_letters
    words = _tokens(normalised)
    input_ngrams = _ngrams(words)
    profiles = _load_profiles()
    candidates = {
        key: profile for key, profile in profiles.items() if profile["script"] == script
    }
    if not candidates:
        return DetectionResult(script, None, round(script_confidence, 6), ())

    character_counts = Counter(normalised)
    word_counts = Counter(words)
    raw_scores: dict[str, float] = {}
    distinctive_by_language: dict[str, float] = {}
    cues_by_language: dict[str, float] = {}
    unique_cues_by_language: dict[str, float] = {}
    for profile in candidates.values():
        language = profile["language_code"]
        distance = _rank_distance(input_ngrams, profile["ngrams"])
        distinctive = sum(
            character_counts[character] * weight
            for character, weight in DISTINCTIVE_CHARACTERS[language].items()
        ) / math.sqrt(max(1, script_letters))
        cue_score = sum(
            min(word_counts[word], 3) for word in CUE_WORDS[language]
        ) / math.sqrt(max(1, len(words)))
        unique_cue_score = sum(
            min(word_counts[word], 3) for word in UNIQUE_CUE_WORDS[language]
        ) / math.sqrt(max(1, len(words)))
        # A language can have multiple profile keys only if future variants are
        # added. Keep its best matching language/script profile.
        score = (
            -7.0 * distance
            + 1.25 * distinctive
            + 0.9 * cue_score
            + (5.0 * unique_cue_score if len(words) == 1 else 0.0)
        )
        raw_scores[language] = max(raw_scores.get(language, -math.inf), score)
        distinctive_by_language[language] = max(
            distinctive_by_language.get(language, 0.0), distinctive
        )
        cues_by_language[language] = max(cues_by_language.get(language, 0.0), cue_score)
        unique_cues_by_language[language] = max(
            unique_cues_by_language.get(language, 0.0), unique_cue_score
        )

    alternatives = _softmax(raw_scores)
    best = alternatives[0]
    resolved = _language_is_resolved(
        alternatives,
        len(words),
        script_letters,
        script_confidence,
        distinctive_by_language[best.language_code],
        cues_by_language[best.language_code],
    )
    if not resolved and script == "Latn" and len(words) <= 3:
        second = alternatives[1].score if len(alternatives) > 1 else 0.0
        resolved = (
            unique_cues_by_language[best.language_code] >= 0.50
            and best.score >= 0.30
            and best.score - second >= 0.10
        )
    direct_evidence = (
        distinctive_by_language[best.language_code] > 0.0
        or unique_cues_by_language[best.language_code] > 0.0
    )
    if (best.language_code == "pcm" or script == "Deva") and not direct_evidence:
        resolved = False
    language_code = best.language_code if resolved else None
    confidence = best.score * script_confidence if resolved else script_confidence
    return DetectionResult(
        script,
        language_code,
        round(confidence, 6),
        tuple(alternatives),
    )


def _mixed_boundaries(text: str) -> list[int]:
    boundaries = {0, len(text)}
    boundaries.update(match.end() for match in CLAUSE_BOUNDARY_PATTERN.finditer(text))

    previous_script: str | None = None
    for index, script in _script_characters(text):
        if previous_script is not None and script != previous_script:
            boundaries.add(index)
        previous_script = script
    return sorted(boundaries)


def _initial_segments(text: str) -> list[DetectionSegment]:
    segments: list[DetectionSegment] = []
    pending_prefix: int | None = None
    boundaries = _mixed_boundaries(text)
    for start, end in zip(boundaries, boundaries[1:]):
        if start == end:
            continue
        value = text[start:end]
        detection = detect(value)
        if detection.script is None:
            if segments:
                previous = segments[-1]
                segments[-1] = DetectionSegment(
                    previous.start,
                    end,
                    text[previous.start:end],
                    previous.detection,
                )
            elif pending_prefix is None:
                pending_prefix = start
            continue

        if pending_prefix is not None:
            start = pending_prefix
            value = text[start:end]
            pending_prefix = None
        segments.append(DetectionSegment(start, end, value, detection))

    if not segments and text:
        return [DetectionSegment(0, len(text), text, detect(text))]
    return segments


def _merge_equivalent_segments(
    text: str, segments: list[DetectionSegment]
) -> tuple[DetectionSegment, ...]:
    if not segments:
        return ()

    merged: list[DetectionSegment] = []
    group_start = segments[0].start
    group_end = segments[0].end
    group_signature = (segments[0].script, segments[0].language_code)
    for segment in segments[1:]:
        signature = (segment.script, segment.language_code)
        if signature == group_signature:
            group_end = segment.end
            continue

        combined_text = text[group_start:group_end]
        merged.append(
            DetectionSegment(
                group_start,
                group_end,
                combined_text,
                detect(combined_text),
            )
        )
        group_start = segment.start
        group_end = segment.end
        group_signature = signature

    combined_text = text[group_start:group_end]
    merged.append(
        DetectionSegment(
            group_start,
            group_end,
            combined_text,
            detect(combined_text),
        )
    )
    return tuple(merged)


def detect_mixed(text: str) -> MixedDetectionResult:
    """Detect ordered script/language spans while retaining a whole-text result.

    Script transitions always create a candidate boundary. Strong sentence or
    clause punctuation creates candidates for language changes within one
    script. Adjacent spans with the same resolved signature are merged again.
    """
    primary = detect(text)
    segments = _merge_equivalent_segments(text, _initial_segments(text))
    return MixedDetectionResult(primary, segments)
