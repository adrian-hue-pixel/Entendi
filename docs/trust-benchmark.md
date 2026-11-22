# What can Entendi verify about an official letter?

**Entendi benchmark v1 · 22 November 2026**

Official notices often ask the reader to act by a particular date or pay an exact amount. A plain-language explanation can make that easier, especially when the letter is in a language the reader is still learning. It can also make a mistake sound more certain than the original. Two small changes, swapping a day and month or moving a decimal point, can change what the reader does. Entendi separates the explanation from the evidence that supports it and flags details it cannot confirm.

This report measures the deterministic part of that safety design. It does not estimate the accuracy of any vision or translation provider. The optional image benchmark is available for a later study with a named provider and model.

## 1. Method

Entendi accepts a photo and asks the configured vision service for a transcription, a structured explanation, and exact excerpts for the due date and amount. The application then checks exact values locally using the following steps.

- **Extract and compare.** A candidate date or amount must match what the regular expressions read from a cited excerpt, and that excerpt must also appear in the transcription. The parser preserves currency and compares amounts as decimal values. It recognizes full-width digits, Japanese/Chinese year–month–day text, German dotted dates, named French and Spanish months, and ISO dates. Recognized issue-date labels are rejected as deadline evidence.
- **Keep ambiguity visible.** A numeric date such as `03/04/2026` can denote two different days. Without an explicit format instruction, Entendi withholds the deadline and asks the reader to confirm with the office. A calendar export needs a verified date. A printed amount that fails verification is withheld as well.
- **Check translation drift.** For a non-English explanation, Entendi requests a separate English back-translation without passing the English anchor into that request. It compares dates, amounts, a basic negation signal, and token overlap against the English restatement produced during extraction. A material difference triggers review. If the second call fails or the English anchor is absent, the check is marked unavailable. The check can catch numerical drift while allowing a similar paraphrase. It can also miss a wrong action that shares the same words.
- **Minimize retained data.** The photo is processed in a temporary app session and sent to the selected provider, so provider handling matters. Entendi does not write the photo into My Letters or exports. A separate redactor masks recognized IBANs, phone numbers, emails, card-like digits, labelled passport numbers, UK National Insurance numbers, and long numeric identifiers before the extracted text is displayed or retained. The last four alphanumeric characters are visible. This step does not remove personal data from image pixels before the provider reads them.

The evidence checker does not certify that a letter is genuine. The confidence banner tells the user what needs checking without implying that the app has independently confirmed the actual image.

## 2. Benchmark and protocol

The dataset consists of 180 fictional notices created from text templates. No genuine letter or personal identifier was used. The benchmark split has 144 notices across English, Spanish, French, German, Simplified Chinese, and Japanese. Each language contributes 24 notices with parallel scenario counts. Hindi, Tamil, and Thai each have another 12 unscored fixtures. They are supplied for later experiments and are not part of the language results below.

The generator assigns a known date and amount before formatting the document. It includes an issue date as a distractor and varies the office name, numeric values, date and amount notation. Some cases have no deadline, no amount, or an ambiguous deadline. These cases test whether the parser abstains in the right circumstances. The labels do not come from the parser.

For this first run, I passed the **gold evidence lines** to the rules. A field counted as correct if the normalized date or currency/decimal pair matched the label exactly. Withholding a value counted as correct only when the label was null. The ambiguous-date flag was scored separately. I also tested deliberate wrong candidates by shifting a date one day, adding one unit to a proposed amount, and proposing a real issue date instead of the deadline. The tests ran without OCR or API calls. Therefore, the experiment measures agreement given the correct evidence location, not whether an AI model can find that location in a document.

## 3. Measured results

| Source language | Notices | Exact deadlines | Exact amounts | Ambiguous dates flagged |
| --- | ---: | ---: | ---: | ---: |
| English | 24 | 23 | 24 | 3/3 |
| Spanish | 24 | 23 | 24 | 3/3 |
| French | 24 | 23 | 24 | 3/3 |
| German | 24 | 23 | 24 | 3/3 |
| Simplified Chinese | 24 | 23 | 24 | 3/3 |
| Japanese | 24 | 23 | 24 | 3/3 |
| **Total** | **144** | **138/144 (95.8%)** | **144/144 (100%)** | **18/18** |

The verifier rejected 114 of 114 shifted candidate dates and 138 of 138 altered amounts. It rejected 114 of 114 printed issue dates with recognized labels. When the same distractor date was placed in an unrelated but genuine excerpt without a recognized label, all 114 of those candidate dates were accepted. The resulting pattern is clear enough to act on in the app. Regex can spot disagreements between values and citations, but cannot reliably tell whether a real date in a letter is the date the reader should act on.

On five direct comparator probes, unchanged English wording passed. A changed date, a changed amount, and removed negation each triggered review. A swapped action with the same words passed. These probes test the comparator, not the quality of machine translation.

## 4. Failures and limits

The six deadline errors were withheld dates written as `YYYY/MM/DD`. This shape is unambiguous, but the current parser accepts year-first ISO hyphens only. Each of the six parallel language groups contains one of these cases. The equal scores reflect scenario construction rather than a finding that the six languages are equally easy to read. One useful follow-up is to extend the supported form and test it on a new held-out set rather than improve the same published score after seeing the examples.

The amount score applies only to the currencies and formats used in these synthetic notices. The app has unit tests for additional symbols, but the table makes no accuracy claim for them. The benchmark also has no crossed-out amounts, arrows, attached pages, handwriting, images photographed at an angle, or local calendar conversions. Real notices with multiple legitimate payment values could defeat the evidence selection step even if the parser itself works.

Round-trip translation is a warning signal. The English anchor and the translation can share an original extraction mistake. A correct paraphrase can have low word overlap, and a wrong action can reuse most of the same words. Confirm uncertain dates, amounts and obligations with the issuing office. PII patterns likewise miss names, addresses and new identifier formats. They should not be treated as anonymization.

A provider-backed run should report OCR accuracy, extraction errors, the effect of the trust checks on wrong answers and abstentions, and the per-language sample counts. Chinese, Japanese, and Thai would benefit from a follow-up that measures character recognition under blur, skew and mixed fonts. No provider or named model has been measured in this release.

## 5. Reproduce the numbers

From the repository root, create a virtual environment and install `requirements.txt`. Then run:

```sh
python -m benchmark.generate
python -m benchmark.evaluate --out /tmp/entendi-rules.json
diff -u benchmark/results.rules.json /tmp/entendi-rules.json
python -m unittest discover -s tests -v
```

Use the [raw labels and data dictionary](../benchmark/data) and the [machine-readable results](../benchmark/results.rules.json) to inspect each discrepancy. The optional [image protocol](../benchmark/README.md) describes Noto font setup, rendering, and the environment variables needed to test a chosen vision model. Record the provider, exact model ID and run date with any additional numbers.

UK National Insurance pattern reference: [GOV.UK](https://www.gov.uk/national-insurance/your-national-insurance-number).
