# Language samples

Each language directory contains one or more 1,000-whitespace-token UTF-8
samples and exact source metadata in adjacent `sources.json` or
`sources_flores.json` files. Multiple samples cover scripts, orthographies,
dialects, or regional varieties that map to the same returned language code.

The Persian directory uses the Western Farsi (`pes_1`) UDHR source plus a Dari
FLORES profile; both map to `fa`.
The Turkish directory contains modern Latin-script Turkish and maps to `tr`.

Other multisample directories include:

- Arabic: Modern Standard plus Mesopotamian, Ta’izzi-Adeni, South and North
  Levantine, Najdi, and Egyptian profiles, all returning `ar`;
- Azerbaijani: North Azerbaijani Latin/Cyrillic and South Azerbaijani Arabic,
  all returning `az`;
- Kurdish: Central Kurdish/Sorani Arabic and Northern Kurdish/Kurmanji Latin,
  both returning `ku`;
- Turkmen: Latin and Cyrillic, both returning `tk`;
- Uzbek: Latin and Cyrillic, both returning `uz`.

Uyghur contains four 1,000-token samples, all mapping to `ug`:

- `sample.txt`: source Uyghur Arabic (UEY)
- `sample_latn.txt`: source Uyghur Latin (ULY)
- `sample_cyrl.txt`: UEY converted to Uyghur Cyrillic (UKY)
- `sample_yengi.txt`: UEY converted to the legacy Uyghur New Script (UYY)

The generated samples retain their derivation in `sources.json`; the alphabet
mapping implementation and exhaustive core-letter tests are in
`tools/uyghur_transliteration.py` and `tests/test_uyghur_transliteration.py`.

Most samples are translations of the Universal Declaration of Human Rights from
a pinned revision of the `wooorm/udhr` corpus. Varieties absent there use the
FLORES-200 `dev` split; `devtest` is kept separate for evaluation. The global
language expansion also uses this FLORES split for Bengali, Mandarin Chinese,
French, German, Hausa, Hindi, Indonesian, Japanese, Marathi, Portuguese,
Spanish, Swahili, Telugu, and Vietnamese. Nigerian Pidgin uses the `train` split
of the pinned NaijaSynCor Universal Dependencies treebank, with its `test` split
reserved for evaluation. This material is intended for feature exploration,
not as a large or representative message corpus. See the adjacent source
metadata for provenance and licence details.

Regenerate all samples with:

```powershell
python .\tools\build_samples.py
python .\tools\build_flores_samples.py
python .\tools\build_naija_sample.py
```

To rebuild only one directory, use `--language`, for example:

```powershell
python .\tools\build_samples.py --language persian
python .\tools\build_flores_samples.py --language persian
```
