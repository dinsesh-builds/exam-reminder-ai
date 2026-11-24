# Contributing

This is a small local tool. Issues and patches are welcome.

## Before you open an issue

Include the file type, the approximate file size, your Python version, and what you expected. If a question is wrong, paste the question and the source phrase shown under it.

## Development

```bash
python -m venv .venv
pip install -r requirements.txt
python app.py
```

Open `index.html` in a browser. The page posts to `http://127.0.0.1:8000/analyze`.

## Changes

Keep question generation deterministic and local. Do not add an API key requirement. Escape any note text before it reaches HTML. Add a line to `CHANGELOG.md` under Unreleased.
