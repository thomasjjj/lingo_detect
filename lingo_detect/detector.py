from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files


WORD_PATTERN = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*", re.UNICODE)
CLAUSE_BOUNDARY_PATTERN = re.compile(
    r"(?:\r\n|\r|\n|[.!?;:]+)[\t \f\v]*",
    re.UNICODE,
)
APOSTROPHES = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'"})
SCRIPT_NAMES = {"Arab": "Arabic", "Cyrl": "Cyrillic", "Latn": "Latin"}
LANGUAGE_NAMES = {
    "ar": "Arabic",
    "en": "English",
    "fa": "Persian (Farsi)",
    "ps": "Pashto",
    "ru": "Russian",
    "tg": "Tajik",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "ug": "Uyghur",
    "uz": "Uzbek",
}

CUE_WORDS = {
    "ar": {
        "في", "من", "أن", "على", "إلى", "أو", "لا", "هو", "هي", "هذا",
        "هذه", "الذي", "التي", "كل", "لكل", "كان", "بين", "دون",
    },
    "en": {
        "the", "of", "and", "to", "in", "or", "is", "are", "that", "this",
        "with", "for", "from", "shall", "has", "have", "not", "every", "all",
    },
    "fa": {
        "از", "آن", "این", "است", "با", "برای", "به", "بود", "در", "را",
        "که", "و", "هر", "همه", "هیچ", "یک", "خود", "شود", "دارد", "نیز",
    },
    "ps": {
        "د", "په", "او", "چې", "له", "څوک", "شي", "وي", "نه", "هغه", "سره",
        "يا", "لري", "هر", "کښې", "کې", "يو", "یو", "دي", "ده",
    },
    "ru": {
        "и", "в", "во", "на", "не", "или", "что", "это", "как", "по", "из",
        "к", "с", "для", "он", "она", "имеет", "каждый", "человек", "никто",
    },
    "tg": {
        "ва", "дар", "ба", "ки", "ҳар", "як", "ё", "бо", "дорад", "аз",
        "инсон", "ҳақ", "ин", "шавад", "онҳо", "нест", "барои",
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
}

# Weights are deliberately asymmetric: letters confined to one supported
# orthography carry more evidence than letters shared by related languages.
DISTINCTIVE_CHARACTERS = {
    "ar": {character: 2.3 for character in "ةأإؤئءى"} | {"آ": 1.5},
    "en": {"w": 1.1},
    "fa": {"ۀ": 3.0, "ک": 0.7, "ی": 0.45}
    | {character: 0.3 for character in "پچژگ"},
    "ps": {character: 3.2 for character in "ټځڅډړږښګڼېۍ"}
    | {character: 0.5 for character in "پچژ"},
    "ru": {"ы": 3.0, "щ": 0.5, "ъ": 0.3},
    "tg": {character: 3.0 for character in "ӣҷӯ"}
    | {character: 0.7 for character in "ғқҳ"},
    "uk": {character: 3.2 for character in "іїєґ"},
    "ur": {character: 3.0 for character in "ٹڈڑںھہے"}
    | {character: 0.4 for character in "پچژگ"},
    "ug": {character: 3.2 for character in "ەڭۆۇۈۋې"}
    | {"ى": 1.0}
    | {character: 3.5 for character in "әҗңөүһ"}
    | {character: 4.0 for character in "əƣɵⱨⱪⱬ"}
    | {character: 2.2 for character in "ëé"}
    | {character: 0.45 for character in "ғқ"},
    "uz": {"ў": 6.0, "ʻ": 3.0, "ʼ": 3.0}
    | {character: 0.65 for character in "қғҳ"}
    | {"q": 0.45, "x": 0.35},
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
    if "CYRILLIC" in name:
        return "Cyrl"
    if "LATIN" in name:
        return "Latn"
    return None


def _normalise(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def _tokens(text: str) -> list[str]:
    return WORD_PATTERN.findall(text.translate(APOSTROPHES))


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
    if word_count <= 10:
        return top >= 0.54 and margin >= 0.10
    return top >= 0.45 and margin >= 0.05


def detect(text: str) -> DetectionResult:
    """Detect the highest defensible script/language resolution for ``text``."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalised = _normalise(text)
    script_counts = Counter(
        script
        for character in normalised
        if character.isalpha() and (script := _script_of(character)) is not None
    )
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
        # A language can have multiple profile keys only if future variants are
        # added. Keep its best matching language/script profile.
        score = -7.0 * distance + 1.25 * distinctive + 0.9 * cue_score
        raw_scores[language] = max(raw_scores.get(language, -math.inf), score)
        distinctive_by_language[language] = max(
            distinctive_by_language.get(language, 0.0), distinctive
        )
        cues_by_language[language] = max(cues_by_language.get(language, 0.0), cue_score)

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
    for index, character in enumerate(text):
        if not character.isalpha():
            continue
        script = _script_of(character)
        if script is None:
            continue
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
