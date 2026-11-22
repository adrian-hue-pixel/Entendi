# Entendi

A Streamlit workspace with a dashboard, a calendar, a journal, and tools for keeping notes and comparing items.

## Run locally

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app runs without credentials. Workspace records live in the browser session and can be exported as JSON and imported from the sidebar. Voice recordings can be played back during the current session. File review records save the filename and notes.
