# Entendi

Entendi turns a photo of an official letter into a plain-language explanation in English, Hindi or Tamil. See what the letter asks, find the supporting words, and save dates to your phone calendar. Built for EvoHacks 2.

## Try it

Open [Entendi](https://entendi.streamlit.app/) and choose **Try a sample letter**. Three fictional examples are available on **Understand a Letter**. They work without an API key and cover a payment deadline, an appointment confirmation and an unreadable deadline.

## Run locally

Requires Python 3.10 or later.

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

The app sends a JPEG as an inline image and reads the JSON response from `choices[0].message.content`. Choose an endpoint that supports the [chat-completions image format](https://developers.openai.com/api/reference/resources/chat). No provider is configured by default. Keep credentials out of Git.

## Letters, privacy, and deadlines

- The current photo and transcription are held temporarily by the Streamlit session so you can compare them with the explanation. Real photos go to the configured reading service. Its handling and retention depend on the provider.
- My Letters and exports contain the explanation and extracted facts. They omit the photo, original transcription and source excerpts. **My data** can also contain benefits answers and feedback. Keep downloads private.
- Quote badges indicate a text match against the extracted transcription, not an independent check of the image. Confirm unclear dates and obligations with the issuing office. Entendi does not give legal advice or verify authenticity.
- **Listen** uses offline eSpeak NG on the app server, with no separate audio service. Streamlit Cloud installs it from `packages.txt`. For local setups without eSpeak NG, Listen uses the browser’s on-device voice for the selected language.
- Calendar downloads use all-day events. WhatsApp opens a draft for you to review and send.

## Benefits Check

Benefits Check uses fixed rules for three selected Indian central schemes. The office makes the final decision. See the [National Social Assistance Programme criteria](https://sansad.in/getFile/lsscommittee/Rural%20Development%20and%20Panchayati%20Raj/17_Rural_Development_and_Panchayati_Raj_29.pdf?source=loksabhadocs) and the Ministry of Labour’s [PM-SYM guidance](https://www.labour.gov.in/static/uploads/2025/07/cdc13db52c1398b561576094a81b7b7d.pdf).

## Tests

```sh
python -m unittest discover -s tests
```
