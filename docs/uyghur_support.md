# Uyghur orthography support

The detector maps all supported modern-Uyghur orthographies to ISO 639-1 `ug`:

| Orthography | Abbreviation | ISO 15924 result | Coverage |
|---|---|---|---|
| Uyghur Arabic alphabet | UEY | `Arab` | source corpus and held-out FLORES |
| Uyghur Latin alphabet | ULY/NUL | `Latn` | source corpus and converted held-out FLORES |
| Uyghur Cyrillic alphabet | UKY | `Cyrl` | converted corpus and held-out FLORES |
| Uyghur New Script | UYY | `Latn` | converted corpus and held-out FLORES |

Unicode CLDR lists Arabic, Cyrillic, and Latin as scripts used for `ug`.
Arabic is the official writing system in Xinjiang, Cyrillic remains in use by
Uyghurs in Central Asia, and the modern auxiliary Latin system is widely used
as a reversible romanization. Uyghur New Script is retained for legacy text
even though it is no longer the official orthography.

The detector recognizes ULY spellings with both `ë` and the `é` variant found
in the pinned UDHR source. UYY-specific Latin letters such as `ə`, `ƣ`, `ɵ`,
`ⱨ`, `ⱪ`, and `ⱬ` are strong identifiers. Cyrillic letters such as `ә`, `җ`,
`ң`, `ө`, `ү`, and `һ`, and Arabic letters such as `ە`, `ڭ`, `ۆ`, `ۇ`, `ۈ`,
`ۋ`, and `ې`, provide strong alphabet evidence before word and n-gram scoring.

Historical Old Uyghur script (`Ougr`) is intentionally outside this feature.
It primarily represents the medieval Old Uyghur language, so silently labeling
it as modern `ug` would conflate a language boundary with an orthography change.

Orthography references:

- [Unicode CLDR Languages and Scripts](https://www.unicode.org/cldr/charts/48/supplemental/languages_and_scripts.html)
- [BGN/PCGN 2023 Romanization of Uyghur](https://assets.publishing.service.gov.uk/media/65f317e99d99de001d03df0c/Uyghur_romanization.pdf)
- [The Unicode Standard: Old Uyghur](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-14/#G48768)
