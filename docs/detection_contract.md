# Detection result contract

Language detection should preserve the highest resolution justified by the
input. A detector must not force a language code when it only has enough
evidence for a writing system. Language codes use ISO 639-1 where assigned;
Nigerian Pidgin uses ISO 639-3 `pcm` because it has no ISO 639-1 code. Uyghur
always uses `ug`; its Arabic, Cyrillic, and Latin orthographies are represented
by the ISO 15924 script code in the separate `script` field.

The recommended Python result shape is:

```python
{
    "script": "Cyrl",          # One of the supported ISO 15924 codes
    "language_code": "tg",    # ISO language code, or None when uncertain
    "confidence": 0.91,
    "alternatives": [
        {"language_code": "tg", "score": 0.91},
        {"language_code": "uz", "score": 0.06},
        {"language_code": "ru", "score": 0.03},
    ],
}
```

For a Cyrillic input whose language cannot be resolved safely:

```python
{
    "script": "Cyrl",
    "language_code": None,
    "confidence": 0.99,        # confidence in the script classification
    "alternatives": [
        {"language_code": "tg", "score": 0.38},
        {"language_code": "uz", "score": 0.34},
        {"language_code": "ru", "score": 0.28},
    ],
}
```

`confidence` must describe the returned resolution. When a language is
returned, it is language confidence; for a script-only result, it is script
confidence. Alternatives are ranked evidence scores over only the languages
supported for that script. They should not be described as probabilities until
they have been calibrated against held-out data.

The evaluation harness also accepts a bare language-code string for simple
detectors, but the structured result is the intended public API.

## Mixed-text result

`detect_mixed(text)` preserves the whole-text `detect(text)` result as
`primary`, then returns independent ordered spans:

```python
{
    "primary": {
        "script": "Latn",
        "language_code": None,
        "confidence": 0.69,
        "alternatives": [...],
        "resolution": "script",
        "label": "Latin · uncertain",
    },
    "segments": [
        {
            "start": 0,
            "end": 21,
            "text": "The museum is called ",
            "script": "Latn",
            "language_code": "en",
            "confidence": 0.89,
            "alternatives": [...],
            "resolution": "language",
            "label": "Latin · English",
        },
        {
            "start": 21,
            "end": 46,
            "text": "Государственный Эрмитаж, ",
            "script": "Cyrl",
            "language_code": "ru",
            "confidence": 0.78,
            "alternatives": [...],
            "resolution": "language",
            "label": "Cyrillic · Russian",
        },
    ],
    "scripts": ["Latn", "Cyrl"],
    "language_codes": ["en", "ru"],
    "is_mixed_script": True,
    "is_mixed_language": True,
    "is_mixed": True,
    "has_unresolved_segments": False,
}
```

The conceptual example uses JSON-like lists; the immutable Python result stores
`segments`, `scripts`, and `language_codes` as tuples. `as_dict()` remains JSON
serializable.

Segment offsets are Python string indices satisfying
`original[segment.start:segment.end] == segment.text`. Ordered segment text
concatenates back to the original input. A short embedded proper name may return
a script-only segment with ranked alternatives rather than an unjustified
language. Such a segment makes `has_unresolved_segments` true but can still make
`is_mixed_script` true.

Script transitions always propose a boundary. Strong sentence and clause
punctuation also proposes boundaries so different supported languages using the
same script can be detected in separate clauses. Adjacent spans with matching
script/language resolutions are merged. Consequently, this API is a
conservative span detector, not word-level code-switch tagging.
