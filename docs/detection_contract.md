# Detection result contract

Language detection should preserve the highest resolution justified by the
input. A detector must not force a language code when it only has enough
evidence for a writing system. Uyghur always uses ISO 639-1 `ug`; its Arabic,
Cyrillic, and Latin orthographies are represented by the ISO 15924 script code
in the separate `script` field.

The recommended Python result shape is:

```python
{
    "script": "Cyrl",          # ISO 15924 code: Arab, Cyrl, or Latn
    "language_code": "tg",    # ISO 639-1 code, or None when uncertain
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
