# Held-out language-identification cases

`flores200_devtest.jsonl` contains deterministic cases for these dimensions:

- language: `ar`, `az`, `bn`, `de`, `en`, `es`, `fa`, `fr`, `ha`, `he`, `hi`,
  `hy`, `id`, `ja`, `ka`, `kk`, `ku`, `ky`, `mr`, `pa`, `pcm`, `ps`, `pt`,
  `ru`, `sd`, `sw`, `te`, `tg`, `tk`, `tr`, `ug`, `uk`, `ur`, `uz`, `vi`,
  `yi`, `zh`
- whitespace-token length: 1, 2, 3, 5, 10, 20, 50, 100

The 43 FLORES language/variety configurations produce 1,720 cases. Another 40
Nigerian Pidgin cases come from the NaijaSynCor test split, 40 native Cyrillic
Uzbek cases come from Tatoeba, and 40 Northern Pashto cases come from held-out
UDHR text. The 40 Uyghur Arabic cases have three parallel alphabet conversions,
adding 120. Disjoint UDHR suffixes add 16 Azerbaijani Cyrillic, 24 Kurmanji, 40
Western Punjabi, and 8 Turkmen Cyrillic cases. The complete suite therefore has
2,048 cases.

The packaged n-gram profiles do not use these case texts. Detector weights and
resolution thresholds have, however, been iteratively checked against this
suite, so it is a development benchmark rather than an untouched final test.
Use an independent message-domain corpus to estimate operational accuracy.

The source is the `devtest` split of FLORES-200, downloaded from
`https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz`. The archive is
verified against SHA-256
`b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6`.
FLORES-200 is licensed under CC BY-SA 4.0. Each case retains its FLORES language
code and one-based source sentence range for attribution and reproducibility.

The Persian cases use FLORES Western Persian (`pes_Arab`) and map to the ISO
639-1 code `fa`. They are independent of the Western Farsi UDHR text used to
build the detector profile.

Turkish uses FLORES modern Latin-script Turkish (`tur_Latn`) and maps to `tr`.
These cases are independent of the Turkish UDHR profile corpus.

Regional FLORES coverage includes six colloquial Arabic varieties in addition
to Modern Standard Arabic; North and South Azerbaijani; Dari; Central Kurdish;
Hebrew; Armenian; Georgian; Kazakh; Kyrgyz; Sindhi; Turkmen; and Eastern
Yiddish. The corresponding profiles use FLORES `dev` only where the pinned UDHR
checkout lacks the required variety, while these cases use `devtest`.

The added global-language profiles use FLORES-200 `dev`, while their evaluation
cases use `devtest`. Mandarin Chinese is represented by Simplified Chinese
`zho_Hans`; the detector reports the generic Han script code `Hani` because
individual shared Han characters do not establish an orthographic variant.
Japanese reports `Jpan`, grouping Han characters with kana when kana provide
Japanese context.

Nigerian Pidgin uses ISO 639-3 `pcm` because no ISO 639-1 code is assigned. Its
profile comes from the `train` split of the NaijaSynCor Universal Dependencies
treebank, and these evaluation cases use its disjoint `test` split. The source
revision and SHA-256 hashes are pinned in `tools/build_test_samples.py`;
NaijaSynCor is licensed under CC BY-SA 4.0.

Disjoint post-prefix UDHR cases cover Azerbaijani Cyrillic, Kurmanji Latin,
Western Punjabi/Shahmukhi, and Turkmen Cyrillic. Their per-case token ranges are
recorded and do not overlap the 1,000-token profile prefix or one another.

FLORES supplies Southern Pashto (`pbt_Arab`), while the additional held-out UDHR
cases supply Northern Pashto (`pbu`); both map to the ISO 639-1 code `ps`.
FLORES-200 supplies Latin-script Northern Uzbek. Independent native Cyrillic
Uzbek sentences come from Tatoeba's per-language `uzb` export under CC BY 2.0
FR; the downloaded archive is pinned by SHA-256 in
`tools/build_test_samples.py`. Both scripts map to `uz`.

FLORES supplies Uyghur Arabic (`uig_Arab`). Its Uyghur Latin (ULY), Uyghur
Cyrillic (UKY), and Uyghur New Script (UYY) cases are deterministic alphabet
conversions of the same held-out sentences. This gives exact parallel coverage
at every test length, but it tests orthographic recognition rather than the
regional vocabulary differences found in independently authored Central Asian
Cyrillic Uyghur. Every converted case records the transformation in its source
metadata.

The UDHR sources are from the copyright-free package pinned to commit
`d3d38276c91668df9ac4e33e5dac7cd3a14c12b2`.

Regenerate the data with:

```powershell
python .\tools\build_test_samples.py
```

The evaluator separately reports exact-language results, correct script-only
fallbacks, and wrong answers. Evaluate a detector callable with:

```powershell
python .\tools\evaluate_detector.py --detector package.module:function
```
