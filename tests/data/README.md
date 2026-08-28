# Held-out language-identification cases

`flores200_devtest.jsonl` contains five deterministic cases for every
combination of these dimensions:

- language: `ar`, `en`, `ps`, `ru`, `tg`, `uk`, `ur`, `uz`
- whitespace-token length: 1, 2, 3, 5, 10, 20, 50, 100

The core FLORES matrix produces 320 cases. Another 40 native Cyrillic Uzbek
cases come from Tatoeba's Uzbek export. A final 40 Northern Pashto cases use the
non-overlapping portion of the pinned UDHR text after the 1,000-token training
prefix. The complete suite therefore has 400 cases. Do not use this file to
train or tune the detector; it is an evaluation set.

The source is the `devtest` split of FLORES-200, downloaded from
`https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz`. The archive is
verified against SHA-256
`b8b0b76783024b85797e5cc75064eb83fc5288b41e9654dabc7be6ae944011f6`.
FLORES-200 is licensed under CC BY-SA 4.0. Each case retains its FLORES language
code and one-based source sentence range for attribution and reproducibility.

FLORES supplies Southern Pashto (`pbt_Arab`), while the additional held-out UDHR
cases supply Northern Pashto (`pbu`); both map to the ISO 639-1 code `ps`.
FLORES-200 supplies Latin-script Northern Uzbek. Independent native Cyrillic
Uzbek sentences come from Tatoeba's per-language `uzb` export under CC BY 2.0
FR; the downloaded archive is pinned by SHA-256 in
`tools/build_test_samples.py`. Both scripts map to `uz`.

The additional Northern Pashto source is the copyright-free UDHR package pinned
to commit `d3d38276c91668df9ac4e33e5dac7cd3a14c12b2`. Its test token ranges are
recorded in every case and are disjoint from both the 1,000-token training prefix
and one another.

Regenerate the data with:

```powershell
python .\tools\build_test_samples.py
```

The evaluator separately reports exact-language results, correct script-only
fallbacks, and wrong answers. Evaluate a detector callable with:

```powershell
python .\tools\evaluate_detector.py --detector package.module:function
```
