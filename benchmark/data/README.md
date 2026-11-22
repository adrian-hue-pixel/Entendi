# Entendi Synthetic Official Notices v1

This dataset contains **180 fictional, labelled notices**. All text was generated from hand-written templates and a fixed pseudorandom seed. It contains no real notices, personal data, signatures, or official endorsements.

| Split | Languages | Notices |
| --- | --- | ---: |
| Benchmark | English, Spanish, French, German, Simplified Chinese, Japanese | 144 (24 each) |
| Exploratory | Hindi, Tamil, Thai | 36 (12 each, currently unscored) |

Each line of `notices.jsonl` is one UTF-8 JSON object.

| Field | Meaning |
| --- | --- |
| `id`, `language`, `split` | Stable identifier, source-language code and evaluation split |
| `text` | Full fictional notice |
| `deadline` | ISO date, or null when absent or ambiguous |
| `currency`, `amount` | ISO-style currency code and exact decimal string, both null when absent |
| `deadline_source`, `amount_source` | Annotated evidence lines, empty if absent |
| `issue_date` | Labelled distractor |
| `scenario` | Formatting or ambiguity case |

The gold values come from the generator before formatting. The text-rule baseline receives the labelled evidence lines. It tests normalization and evidence agreement, not OCR, source localization or model performance. The six benchmark languages use parallel templates and equal case counts, so identical scores do not imply comparable real-world OCR difficulty. No results are reported for Hindi, Tamil or Thai.

From a fresh clone, install `requirements.txt` and run `python -m benchmark.generate` followed by `python -m benchmark.evaluate --out /tmp/entendi-results.json`. For the optional image benchmark, see the [evaluation instructions and write-up](https://github.com/adrian-hue-pixel/Entendi/tree/main/benchmark).

Licence: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). Code in the main repository uses MIT.
