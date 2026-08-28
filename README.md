# lingo-detect

A dependency-free, script-first detector for Arabic, English, Pashto, Russian,
Tajik, Ukrainian, Urdu, and Uzbek. Uzbek is supported in Latin and Cyrillic.

The detector returns the highest resolution justified by the input. Ambiguous
text therefore returns a known script with no forced language instead of a
confident-looking wrong answer.

```python
from lingo_detect import detect

result = detect("ҳар як инсон ҳақ дорад")
print(result.label)       # Cyrillic · Tajik
print(result.as_dict())
```

A script-only result looks like:

```python
{
    "script": "Cyrl",
    "language_code": None,
    "confidence": 1.0,
    "alternatives": ...,
    "resolution": "script",
    "label": "Cyrillic · uncertain",
}
```

Run the tests and held-out evaluation with:

```powershell
python -m unittest discover -s .\tests -v
python .\tools\evaluate_detector.py
```

Rebuild generated profiles or evaluation data with:

```powershell
python .\tools\build_language_profiles.py
python .\tools\build_test_samples.py
```

See `docs/detection_contract.md` for the complete result contract and
`tests/data/README.md` for evaluation provenance and limitations.
