# Language samples

Each language directory contains a 1,000-whitespace-token UTF-8 sample in
`sample.txt` and exact source metadata in `sources.json`. Uzbek also contains a
1,000-token Cyrillic sample because both Latin and Cyrillic Uzbek occur in real
input; both map to `uz`.

The Persian directory uses the Western Farsi (`pes_1`) UDHR source, rather than
the separate Dari (`pes_2`) source in the upstream package, and maps to `fa`.

Uyghur contains four 1,000-token samples, all mapping to `ug`:

- `sample.txt`: source Uyghur Arabic (UEY)
- `sample_latn.txt`: source Uyghur Latin (ULY)
- `sample_cyrl.txt`: UEY converted to Uyghur Cyrillic (UKY)
- `sample_yengi.txt`: UEY converted to the legacy Uyghur New Script (UYY)

The generated samples retain their derivation in `sources.json`; the alphabet
mapping implementation and exhaustive core-letter tests are in
`tools/uyghur_transliteration.py` and `tests/test_uyghur_transliteration.py`.

All samples are translations of the Universal Declaration of Human Rights from
a pinned revision of the `wooorm/udhr` corpus. This alignment greatly reduces
topic bias. They are intended for feature exploration and tests, not as a large
or representative training corpus. See each `sources.json` and the source
repository for provenance and licence details.

Regenerate all samples with:

```powershell
python .\tools\build_samples.py
```

To rebuild only one directory, use `--language`, for example:

```powershell
python .\tools\build_samples.py --language persian
```
