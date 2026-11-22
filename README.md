# Entendi

Entendi turns a photo of an official letter into a plain-language explanation in 17 languages across Europe and Asia, including Hindi. See what the letter asks, find the supporting words, and save dates to your phone calendar. Built for EvoHacks 2.

## Try it

Open [Entendi](https://entendi.streamlit.app/) and choose **Try a sample letter**. Three fictional examples are available on **Understand a Letter**. They work without an API key and cover a payment deadline, an appointment confirmation and an unreadable deadline.

## Country and language

On the first visit, select a country and an interface language. The picker includes Europe and Asia, the named countries elsewhere, and an Other option. Countries with several supported languages prompt for a choice. The selectable explanation languages use their own names. Edit preferences from the sidebar, or use **My data** to take the profile and saved letters to another session. No email, login, account database or cloud profile is required.

Country settings are hints for document formats and issuer vocabulary. The app never guesses a deadline from an ambiguous date. Local date display and decimal formatting preserve the original currency. Country-specific masking supplements the generic privacy rules, with local patterns supported selectively. Benefits are available for **England**, selected within the United Kingdom. App labels and common messages are static catalogues in `locales/`. English is used for entries that lack a translation, including some secondary captions.

## Owl voice and translation maintenance

The owl uses fixed public phrases only. It displays an English line and an interface-language line, each with its own Listen button. The six benchmark locales have an in-project meaning check recorded in the JSON files. The other locales are marked machine translated. Independent native-speaker review is welcome.

The deploy checks for pre-generated clips under `assets/owl_audio/`, otherwise prepares them in the background and shares the per-language cache. The voice comes from gTTS when reachable, with offline speech as a fallback. Personal letter audio stays on the offline speech path.

With network access, `python -m owl_audio --language English --language Japanese` produces MP3 files to include with a release. Running without `--language` generates all clips. The file names depend on the translated wording so revised lines will get fresh audio. The checked-in strings can be regenerated once with `python -m translate_owl --language Japanese` using `GEMINI_LOCALE_API_KEY` and `GEMINI_LOCALE_MODEL`. Review any regenerated wording before shipping. Gemini is not a runtime translation dependency.

## Run locally

Requires Python 3.11 or later.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Enable real-photo reading

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in these values. On Streamlit Community Cloud, use the app’s Secrets settings instead. Environment variables of the same names also work.

| Setting | Value |
| --- | --- |
| `LETTER_API_URL` | Full HTTPS URL of an OpenAI-compatible chat-completions endpoint that accepts image inputs |
| `LETTER_API_MODEL` | A vision-capable model ID supported by that endpoint |
| `LETTER_API_KEY` | Bearer token if the endpoint requires one |

Choose any of the 17 output languages. A vision provider can accept other source languages, but the local verifier only confirms supported date and amount formats. The app sends a JPEG as an inline image and reads the JSON response from `choices[0].message.content`. Choose an endpoint that supports the [chat-completions image format](https://developers.openai.com/api/reference/resources/chat). No provider is configured by default. Keep credentials out of Git.

## Letters, privacy, and deadlines

- The current photo and transcription are held temporarily by the Streamlit session so you can compare them with the explanation. Real photos go to the configured reading service. Its handling and retention depend on the provider.
- My Letters and exports contain the explanation and extracted facts. They omit the photo, original transcription and source excerpts. **My data** can also contain benefits answers and feedback. Keep downloads private.
- Quote badges indicate a text match against the extracted transcription, not an independent check of the image. Confirm unclear dates and obligations with the issuing office. Entendi does not give legal advice or verify authenticity.
- **Listen** uses offline eSpeak NG on the app server, with no separate audio service. Streamlit Cloud installs it from `packages.txt`. For local setups without eSpeak NG, Listen uses the browser’s on-device voice for the selected language.
- Calendar downloads use all-day events. WhatsApp opens a draft for you to review and send.

## Trust and privacy

Before presenting a due date or amount, Entendi verifies that the value agrees with the quoted text. It withholds ambiguous numeric dates unless the letter states an explicit date format. For translated explanations, a separate English back-translation checks for changes to facts and wording. The check can miss genuine errors, especially when the original evidence is wrong.

Entendi masks all but the last four alphanumeric characters in recognized IBANs, phone numbers, emails, card-like digit strings, labelled passport numbers and UK National Insurance numbers. Source photos are temporarily processed in the session and sent to the configured provider. Prices and deadlines should still be confirmed with the issuing office.

## Benefits Check

England (United Kingdom) is the verified location. Benefits Check explains the age and education routes for [free NHS prescriptions](https://www.nhsbsa.nhs.uk/help-nhs-prescription-costs/free-nhs-prescriptions) and [free NHS sight tests](https://www.nhs.uk/nhs-services/opticians/free-nhs-eye-tests-and-optical-vouchers/). Other routes are available through the official sources. Other countries are marked coming soon.

## Benchmark and write-up

- [Synthetic dataset and data dictionary](benchmark/data)
- [Evaluation instructions](benchmark/README.md) and [measured results](benchmark/results.rules.json)
- [Research write-up](docs/trust-benchmark.md)

The published results measure **six source languages using text and labelled evidence**. No provider-backed OCR or translation scores are claimed. The code is MIT-licensed and the synthetic dataset is CC0.

## Tests

```sh
python -m unittest discover -s tests
```
