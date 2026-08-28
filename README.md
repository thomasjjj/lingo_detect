# lingo-detect

`lingo-detect` is a dependency-free, script-first Python language detector. It
accepts a string with no fixed length limit and returns the highest resolution
the available evidence supports:

- a language and its script when the language is sufficiently clear;
- the script alone when the language is ambiguous; or
- no resolution when the input has no supported letters.

This avoids forcing a confident-looking language code from inputs such as one
common letter. The detector is designed primarily for Middle Eastern, Central
Asian, and adjacent South Caucasian/South Asian languages rather than as a
universal language classifier.

## Features

- Script recognition before language scoring.
- ISO 639-1 language codes and ISO 15924 script codes.
- Ranked language alternatives for the detected script.
- Ordered mixed-language and mixed-script spans with exact character offsets.
- Conservative script-only fallbacks for ambiguous text.
- Different confidence thresholds for very short and longer inputs.
- Unicode normalization and support for common apostrophe variants.
- Multiple orthographies for Uyghur and Uzbek.
- Western Persian/Farsi coverage using ISO 639-1 `fa`.
- Modern Latin-script Turkish coverage using ISO 639-1 `tr`.
- Regional Arabic varieties and multiscript Turkic/Kurdish coverage.
- Armenian, Georgian, and Hebrew script recognition.
- No runtime dependencies or external services.
- Packaged language profiles, so detection works offline.

## Supported languages and writing systems

| Language | Code | Supported script or orthography |
|---|---:|---|
| Arabic | `ar` | Arabic (`Arab`): Modern Standard, Mesopotamian, Ta’izzi-Adeni, South/North Levantine, Najdi, and Egyptian profiles |
| Armenian | `hy` | Armenian (`Armn`) |
| Azerbaijani | `az` | North Azerbaijani Latin and Cyrillic; South Azerbaijani Arabic |
| English | `en` | Latin (`Latn`) |
| Georgian | `ka` | Georgian (`Geor`) |
| Hebrew | `he` | Hebrew (`Hebr`) |
| Kazakh | `kk` | Cyrillic (`Cyrl`) |
| Kurdish | `ku` | Central Kurdish/Sorani Arabic (`Arab`) and Northern Kurdish/Kurmanji Latin (`Latn`) |
| Kyrgyz | `ky` | Cyrillic (`Cyrl`) |
| Persian | `fa` | Arabic (`Arab`): Western Persian/Farsi and Dari profiles |
| Punjabi | `pa` | Western Punjabi/Shahmukhi (`Arab`) |
| Pashto | `ps` | Arabic (`Arab`), including Northern and Southern evaluation coverage |
| Russian | `ru` | Cyrillic (`Cyrl`) |
| Sindhi | `sd` | Arabic (`Arab`) |
| Tajik | `tg` | Cyrillic (`Cyrl`) |
| Turkmen | `tk` | Latin (`Latn`) and Cyrillic (`Cyrl`) |
| Turkish | `tr` | Latin (`Latn`), modern Turkish alphabet |
| Ukrainian | `uk` | Cyrillic (`Cyrl`) |
| Urdu | `ur` | Arabic (`Arab`) |
| Uyghur | `ug` | Uyghur Arabic/UEY (`Arab`), Cyrillic/UKY (`Cyrl`), Latin/ULY (`Latn`), and legacy New Script/UYY (`Latn`) |
| Uzbek | `uz` | Latin (`Latn`) and Cyrillic (`Cyrl`) |
| Yiddish | `yi` | Hebrew (`Hebr`), included as a Hebrew-script confounder |

The same language code is returned across orthographies. For example, both
Latin and Cyrillic Uzbek return `uz`, while all four supported Uyghur
orthographies return `ug`. North and South Azerbaijani both return `az`, Sorani
and Kurmanji both return `ku`, and Western Persian and Dari both return `fa`.
The result does not currently expose a dialect/variety field.

This component classifies language and script only. It does not infer message
intent, ideology, authorship, threat, or reliability; those require separate
analysis and appropriate human review.

## Requirements and installation

Python 3.12 or newer is required.

The runtime package has no third-party dependencies. pip and uv use the same
project metadata, and their environments can be kept side by side.

### pip

Install the project from a local checkout into a pip-managed environment:

```powershell
py -3.12 -m venv .venv-pip
.\.venv-pip\Scripts\Activate.ps1
python -m pip install .
```

For development, install the package in editable mode together with its `dev`
extra:

```powershell
python -m pip install -e ".[dev]"
python -m unittest discover -s .\tests -v
python .\tools\evaluate_detector.py
python -m build --wheel
```

### uv

uv uses its own `.venv` and the committed `uv.lock`, so it can coexist with the
pip environment above. If needed, install it using the
[official uv instructions](https://docs.astral.sh/uv/getting-started/installation/).
Create a locked editable development environment with:

```powershell
uv sync --locked --extra dev
```

Run the same checks and build through uv:

```powershell
uv run --locked python -m unittest discover -s .\tests -v
uv run --locked python .\tools\evaluate_detector.py
uv run --locked --extra dev python -m build --wheel
```

For a non-editable local installation instead, use:

```powershell
uv sync --locked --no-editable
```

The package can also be imported directly while the repository root is the
current working directory.

The supported public interface is currently the Python API: use `detect()` for
one whole-text result or `detect_mixed()` for ordered spans. The scripts under
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
| `script` | `str \| None` | Dominant ISO 15924 script: `Arab`, `Armn`, `Cyrl`, `Geor`, `Hebr`, `Latn`, or `None` |
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
the complete string. `detect_mixed()` performs additional work for each proposed
span, then merges equivalent adjacent results.

The input must be a Python `str`; passing `bytes`, `None`, or another type raises
`TypeError`. An empty string, whitespace, punctuation, or digits alone returns
`resolution == "none"` rather than raising an exception.

## Detecting mixed languages and scripts

Use `detect_mixed()` when one string can contain embedded names, quotations, or
sentences in another language or alphabet:

```python
from lingo_detect import detect_mixed

text = (
    "The museum is called Государственный Эрмитаж, "
    "and it is located in Saint Petersburg."
)
result = detect_mixed(text)

print(result.scripts)         # ('Latn', 'Cyrl')
print(result.language_codes)  # ('en', 'ru')
print(result.is_mixed_script)    # True
print(result.is_mixed_language)  # True

for segment in result.segments:
    print(segment.start, segment.end, segment.label, repr(segment.text))
```

The three returned segments are English, Russian, and English. Their
`start:end` offsets always select the original span, and concatenating every
`segment.text` reconstructs the input exactly. Each `DetectionSegment` exposes
`script`, `language_code`, `confidence`, `resolution`, and `label`, while its
full single-span result remains available as `segment.detection`.

`MixedDetectionResult` provides:

| Field | Meaning |
|---|---|
| `primary` | The unchanged whole-text result that `detect(text)` would return |
| `segments` | Ordered `DetectionSegment` objects covering the input |
| `scripts` | Unique resolved scripts in first-seen order |
| `language_codes` | Unique resolved language codes in first-seen order |
| `is_mixed_script` | Whether more than one supported script was found |
| `is_mixed_language` | Whether more than one language was resolved |
| `is_mixed` | Whether either scripts or languages are mixed |
| `has_unresolved_segments` | Whether any span only reached script or no resolution |

Call `result.as_dict()` to serialize the overall result, summary fields, and
every segment together.

Short names remain conservative. For a Wikipedia-style phrase such as
`Moscow (Russian: Москва)`, the embedded `Москва` span is reliably identified as
Cyrillic, but may return `language_code=None` because the spelling alone is not
unique to Russian. Its ranked alternatives still place `ru` first. Longer
Russian names or phrases can resolve the language directly.

Language changes within the same script are detected at clear sentence or
clause boundaries. For example, an English sentence followed by
`Oʻzbekiston respublikasi mustaqil davlat.` produces `('en', 'uz')` even though
both spans use Latin script.

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
   Unicode names as Arabic, Armenian, Cyrillic, Georgian, Hebrew, or Latin. The
   most frequent script becomes the input's dominant script, and its share of
   all recognized letters becomes the script confidence.
3. **Restrict the candidate set.** Only language profiles registered for the
   dominant script are considered. This prevents, for example, English from
   competing with Tajik for Cyrillic input.
4. **Score distinctive letters.** Orthography-specific characters carry strong
   evidence. Examples include Ukrainian `ї`, Pashto `ښ`, Kurdish `ڕ`, Sindhi
   `ڪ`, Uyghur `ڭ`, Azerbaijani Cyrillic `ҹ`, and Uzbek `ў`. A character stops
   being treated as distinctive when another supported orthography shares it.
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

Closely related languages often share both letters and vocabulary. Persian,
Dari, Urdu, Punjabi, and South Azerbaijani share much of their character set;
the Turkic languages do likewise across Latin and Cyrillic. Those cases rely
especially on cue words and n-gram spelling patterns, and ambiguous short text
falls back to its script.

`detect()` returns one result for the entire input. A Latin acronym inside
otherwise Arabic or Cyrillic text normally does not hide the dominant native
script. Use `detect_mixed()` when the individual spans matter.

Mixed detection first proposes boundaries at changes between supported scripts
and after strong sentence or clause punctuation. Every span is passed through
the same conservative `detect()` pipeline described above. Adjacent spans that
resolve to the same script and language are merged again, preventing ordinary
single-language paragraphs from being fragmented merely because they contain
several sentences.

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
python .\tools\build_flores_samples.py
python .\tools\build_language_profiles.py
```

`build_samples.py` downloads the pinned UDHR material. Regional varieties not
present there are built from FLORES-200's `dev` split by
`build_flores_samples.py`; the separate `devtest` split supplies evaluation
text. Both builders require network access. Rebuilding profiles from existing
local samples does not.

## Evaluation

The development suite contains 1,448 cases covering every supported language at 1,
2, 3, 5, 10, 20, 50, and 100 words. It separately counts exact-language
answers, correct script-only fallbacks, and wrong answers.

Current results for the bundled detector are:

| Outcome | Cases | Rate |
|---|---:|---:|
| Exact language | 991/1,448 | 68.4% |
| Correct script-only fallback | 457/1,448 | 31.6% |
| Useful language or script resolution | 1,448/1,448 | 100.0% |
| Wrong | 0/1,448 | 0.0% |

Across the 20-, 50-, and 100-word buckets, 516/543 cases (95.0%) resolve to the
exact language and the remainder safely return the correct script. Short,
closely related text deliberately accounts for most script-only results.

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

The data builder downloads FLORES-200 and pinned auxiliary sources.
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
  in any supported script may resemble and be assigned to a supported language.
  Validate the regional candidate-set assumption at the application boundary.
- Variety labels are not returned: Arabic varieties share `ar`, Dari and Western
  Persian share `fa`, Kurdish varieties share `ku`, and Azerbaijani varieties
  share `az`.
- Very short words may only resolve to a script, especially when closely related
  languages share letters and vocabulary.
- `detect()` returns one dominant result; callers must opt into segmentation
  with `detect_mixed()`.
- Same-script language changes without a sentence or clause boundary may remain
  one span. This is heuristic span detection, not token-level code-switch
  tagging.
- Short proper names can identify a script without containing enough evidence
  to resolve a language safely; inspect the span's alternatives in that case.
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
