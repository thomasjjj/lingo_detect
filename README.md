# lingo-detect

`lingo-detect` is a dependency-free, script-first Python language detector. It
accepts a string with no fixed length limit and returns the highest resolution
the available evidence supports:

- a language and its script when the language is sufficiently clear;
- the script alone when the language is ambiguous; or
- no resolution when the input has no supported letters.

This avoids forcing a confident-looking language code from inputs such as one
common letter. The detector is designed for a defined set of related Arabic-,
Cyrillic-, and Latin-script languages rather than as a universal language
classifier.

## Features

- Script recognition before language scoring.
- ISO 639-1 language codes and ISO 15924 script codes.
- Ranked language alternatives for the detected script.
- Conservative script-only fallbacks for ambiguous text.
- Different confidence thresholds for very short and longer inputs.
- Unicode normalization and support for common apostrophe variants.
- Multiple orthographies for Uyghur and Uzbek.
- No runtime dependencies or external services.
- Packaged language profiles, so detection works offline.

## Supported languages and writing systems

| Language | Code | Supported script or orthography |
|---|---:|---|
| Arabic | `ar` | Arabic (`Arab`) |
| English | `en` | Latin (`Latn`) |
| Pashto | `ps` | Arabic (`Arab`), including Northern and Southern evaluation coverage |
| Russian | `ru` | Cyrillic (`Cyrl`) |
| Tajik | `tg` | Cyrillic (`Cyrl`) |
| Ukrainian | `uk` | Cyrillic (`Cyrl`) |
| Urdu | `ur` | Arabic (`Arab`) |
| Uyghur | `ug` | Uyghur Arabic/UEY (`Arab`), Cyrillic/UKY (`Cyrl`), Latin/ULY (`Latn`), and legacy New Script/UYY (`Latn`) |
| Uzbek | `uz` | Latin (`Latn`) and Cyrillic (`Cyrl`) |

The same language code is returned across orthographies. For example, both
Latin and Cyrillic Uzbek return `uz`, while all four supported Uyghur
orthographies return `ug`.

## Requirements and installation

Python 3.12 or newer is required.

Install the project from a local checkout:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
```

For development, use an editable installation:

```powershell
python -m pip install -e .
```

The package can also be imported directly while the repository root is the
current working directory.

The supported public interface is currently the Python API. The scripts under
`tools/` are development and evaluation utilities, not a general-purpose text
classification CLI.

## Quick start

```python
from lingo_detect import detect

result = detect("ҳар як инсон ҳақ дорад")

print(result.language_code)  # tg
print(result.script)         # Cyrl
print(result.confidence)     # confidence in the returned language resolution
print(result.resolution)     # language
print(result.label)          # Cyrillic · Tajik
```

`detect()` always returns a `DetectionResult`. It does not return a bare string
or raise an error merely because the language is uncertain.

## Understanding the result

| Field | Type | Meaning |
|---|---|---|
| `script` | `str \| None` | Dominant ISO 15924 script: `Arab`, `Cyrl`, `Latn`, or `None` |
| `language_code` | `str \| None` | ISO 639-1 language code, or `None` when language evidence is insufficient |
| `confidence` | `float` | Confidence in the resolution actually returned |
| `alternatives` | `tuple[LanguageScore, ...]` | Candidates for the dominant script, ordered from strongest to weakest |
| `resolution` | `str` | `language`, `script`, or `none` |
| `label` | `str` | Readable summary such as `Cyrillic · Tajik` |

When `resolution == "language"`, `confidence` describes the chosen language.
When `resolution == "script"`, it describes the script classification instead.
The alternative scores are normalized relative evidence scores among the
supported candidates for that script. They have not yet been statistically
calibrated and should not be presented as real-world probabilities.

### Converting a result to a dictionary or JSON

```python
import json

from lingo_detect import detect

result = detect("هر څوک د آزادۍ حق لري")
payload = result.as_dict()

print(json.dumps(payload, ensure_ascii=False, indent=2))
```

The dictionary also includes the computed `resolution` and `label` properties.

### Handling uncertainty explicitly

```python
from lingo_detect import detect


def identify(text: str) -> str:
    result = detect(text)
    if result.language_code is not None:
        return result.language_code
    if result.script is not None:
        return f"und-{result.script}"
    return "und"


print(identify("а"))          # und-Cyrl
print(identify("123 — !!!"))  # und
```

If an application only wants an exact language, it can use
`result.language_code or "und"`. Applications that benefit from partial
information should preserve `script` and `resolution` as shown above.

### Inspecting alternatives

```python
from lingo_detect import detect

result = detect("bir insan")

for candidate in result.alternatives:
    print(candidate.language_code, candidate.score)
```

Alternatives only contain languages supported for the dominant script. A Latin
result therefore does not include Arabic- or Cyrillic-only candidates.

### Processing many strings

```python
from lingo_detect import detect

texts = [
    "This is an English sentence.",
    "Кожна людина має право на свободу.",
    "ھەر بىر ئىنسان ئەركىن تۇغۇلىدۇ.",
]

results = [detect(text).as_dict() for text in texts]
```

There is no fixed input-length cutoff. Runtime and memory use grow with the
amount of text because letters, tokens, and character n-grams are counted for
the complete string.

The input must be a Python `str`; passing `bytes`, `None`, or another type raises
`TypeError`. An empty string, whitespace, punctuation, or digits alone returns
`resolution == "none"` rather than raising an exception.

## Multiscript examples

These Uyghur examples all resolve to `ug` while retaining their script:

```python
from lingo_detect import detect

detect("ھەر بىر ئىنسان ئەركىن تۇغۇلىدۇ")  # script=Arab, language_code=ug
detect("her bir insan erkin tughulidu")    # script=Latn, language_code=ug
detect("һәр бир инсан әркин туғулиду")    # script=Cyrl, language_code=ug
detect("ⱨər bir insan ərkin tuƣulidu")    # script=Latn, language_code=ug
```

Uzbek likewise uses one language code for both supported scripts:

```python
detect("oʻzbekiston respublikasi")       # script=Latn, language_code=uz
detect("ҳар бир инсон ҳуқуқига эгадир")  # script=Cyrl, language_code=uz
```

## How detection works

Detection proceeds from the most reliable orthographic evidence to the more
language-specific statistical evidence.

1. **Normalize the input.** Text is normalized with Unicode NFKC and
   case-folded. Several typographic apostrophes are treated consistently during
   tokenization.
2. **Recognize scripts.** Alphabetic characters are classified from their
   Unicode names as Arabic, Cyrillic, or Latin. The most frequent script becomes
   the input's dominant script, and its share of all recognized letters becomes
   the script confidence.
3. **Restrict the candidate set.** Only language profiles registered for the
   dominant script are considered. This prevents, for example, English from
   competing with Tajik for Cyrillic input.
4. **Score distinctive letters.** Orthography-specific characters carry strong
   evidence. Examples include Ukrainian `ї`, Pashto `ښ`, Urdu `ٹ`, Uyghur `ڭ`
   and `ү`, and Uzbek `ў`.
5. **Score cue words.** Frequent function words and language-specific lexical
   cues contribute additional evidence when individual letters are shared.
6. **Compare character n-grams.** Word-boundary-aware character sequences of
   length two, three, and four are compared with ranked profiles generated from
   the corpora. This captures common spelling and morphological patterns without
   requiring a dictionary match.
7. **Combine and rank the evidence.** N-gram similarity, distinctive letters,
   and cue words produce a score for each supported candidate. The scores are
   normalized and returned in descending order as `alternatives`.
8. **Choose the defensible resolution.** The top score, its margin over the
   second candidate, input length, script confidence, and direct letter/word
   evidence determine whether to return a language. Short inputs require much
   stronger evidence; otherwise the detector returns the script alone.

For mixed-script strings, the detector returns one result for the entire input;
it is not a language segmenter. A Latin acronym inside otherwise Arabic or
Cyrillic text normally does not hide the dominant native script. For heavily
mixed text, inspect `script`, `confidence`, and `resolution` rather than assuming
the result describes every span.

## Corpora and generated profiles

The exploration corpora live under `corpora/`. Each base sample contains 1,000
whitespace-delimited tokens from a pinned Universal Declaration of Human Rights
source, with provenance in the adjacent `sources.json`. Multiple samples are
included for languages with multiple supported orthographies.

The detector does not scan corpus files at runtime.
`tools/build_language_profiles.py` converts them into the ranked character
n-gram data packaged as `lingo_detect/profiles.json`, which is loaded once and
cached on first use.

Useful corpus commands are:

```powershell
python .\tools\analyze_samples.py
python .\tools\build_samples.py
python .\tools\build_language_profiles.py
```

`build_samples.py` downloads the pinned upstream material, so it requires
network access. Rebuilding profiles from existing local samples does not.

## Evaluation

The held-out suite contains 560 cases covering every supported language at 1,
2, 3, 5, 10, 20, 50, and 100 words. It separately counts exact-language
answers, correct script-only fallbacks, and wrong answers.

Current results for the bundled detector are:

| Outcome | Cases | Rate |
|---|---:|---:|
| Exact language | 436/560 | 77.9% |
| Correct script-only fallback | 124/560 | 22.1% |
| Useful language or script resolution | 560/560 | 100.0% |
| Wrong | 0/560 | 0.0% |

All cases of 20, 50, and 100 words resolve to the exact language in this suite.
Short ambiguous text deliberately accounts for most script-only results.

Run the tests and evaluator with:

```powershell
python -m unittest discover -s .\tests -v
python .\tools\evaluate_detector.py
```

Evaluate another compatible detector callable with:

```powershell
python .\tools\evaluate_detector.py --detector package.module:function
```

Rebuild the deterministic evaluation data with:

```powershell
python .\tools\build_test_samples.py
```

The data builder downloads FLORES-200 and current pinned auxiliary sources.
Read `tests/data/README.md` before interpreting the figures: some multiscript
Uyghur cases are parallel alphabet conversions, and the small aligned corpora
and benchmark do not represent every domain or dialect.

## Extending the detector

Adding another language or orthography generally requires:

1. adding a representative UTF-8 sample and provenance under `corpora/`;
2. registering that sample in `tools/build_language_profiles.py`;
3. adding its language name, cue words, and distinctive characters in
   `lingo_detect/detector.py`;
4. rebuilding `lingo_detect/profiles.json`;
5. adding independent held-out cases and detector tests; and
6. running the complete evaluator to check both new accuracy and regressions.

A language may have more than one profile for the same script. The detector
keeps that language's best matching profile before ranking it against other
languages, which is how multiple Latin Uyghur orthographies can share `ug`.

## Limitations

- This is a closed candidate set, not universal language identification.
- Unsupported scripts return no resolution, but an unsupported language written
  in Arabic, Cyrillic, or Latin may resemble and be assigned to a supported
  language. Validate the supported-language assumption at the application
  boundary.
- Very short words may only resolve to a script, especially when closely related
  languages share letters and vocabulary.
- The detector returns one dominant result and does not segment mixed-language
  or code-switched input.
- Alternative scores and confidence values are not yet calibrated probabilities.
- Accuracy can vary by topic, dialect, spelling convention, and source quality.

## Project references

- [Detection result contract](docs/detection_contract.md) defines the public
  result semantics.
- [Uyghur support](docs/uyghur_support.md) explains the supported Uyghur
  orthographies.
- [Corpus documentation](corpora/README.md) describes training-sample scope and
  provenance.
- [Evaluation-data documentation](tests/data/README.md) describes benchmark
  construction and limitations.
- [TODO](TODO.md) records planned calibration and unsupported-script work.

Build a wheel with:

```powershell
py -3.12 -m build
```
