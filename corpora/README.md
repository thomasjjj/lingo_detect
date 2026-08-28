# Language samples

Each language directory contains a 1,000-whitespace-token UTF-8 sample in
`sample.txt` and exact source metadata in `sources.json`. Uzbek also contains a
1,000-token Cyrillic sample because both Latin and Cyrillic Uzbek occur in real
input; both map to `uz`.

All samples are translations of the Universal Declaration of Human Rights from
a pinned revision of the `wooorm/udhr` corpus. This alignment greatly reduces
topic bias. They are intended for feature exploration and tests, not as a large
or representative training corpus. See each `sources.json` and the source
repository for provenance and licence details.

Regenerate all samples with:

```powershell
python .\tools\build_samples.py
```
