# lingo-detect

A dependency-free, script-first detector for Arabic, English, Pashto, Russian,
Tajik, Ukrainian, Urdu, Uyghur, and Uzbek. Uyghur (`ug`) is supported in its
Arabic, Latin, and Cyrillic scripts, including both current Uyghur Latin and the
legacy Latin-derived Uyghur New Script. Uzbek is supported in Latin and
Cyrillic.

The detector returns the highest resolution justified by the input. Ambiguous
text therefore returns a known script with no forced language instead of a
confident-looking wrong answer.

```python
from lingo_detect import detect

result = detect("ҳар як инсон ҳақ дорад")
print(result.label)       # Cyrillic · Tajik
print(result.as_dict())
```

All of these resolve to `ug`:

```python
detect("ھەر بىر ئىنسان ئەركىن تۇغۇلىدۇ")  # Uyghur Arabic (UEY)
detect("her bir insan erkin tughulidu")    # Uyghur Latin (ULY)
detect("һәр бир инсан әркин туғулиду")    # Uyghur Cyrillic (UKY)
detect("ⱨər bir insan ərkin tuƣulidu")    # Uyghur New Script (UYY)
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

See `docs/detection_contract.md` for the complete result contract,
`docs/uyghur_support.md` for the Uyghur orthography scope, and
`tests/data/README.md` for evaluation provenance and limitations.
