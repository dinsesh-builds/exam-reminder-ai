# Exam Reminder AI

Upload class notes and get practice questions plus a revision schedule. The local path runs without an API key.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open `index.html` in a browser. The page posts to `http://127.0.0.1:8000/analyze`. The API also exposes `GET /` as a health check.

## What it does

- Extracts text from an uploaded PDF, image, or text file in `ocr_service.py`. PDFs use pdfplumber. Images use Tesseract OCR.
- Finds definitions, comparisons, numbered lists, formulas, bold terms, and the most repeated topics.
- Builds questions locally from those findings, with difficulty and marks attached.
- If an exam date is supplied, builds a revision schedule of up to 14 days.

The question generator in `app.py` is rule based. `llm_client.py` is an optional OpenAI path and is not called by the running app. No key is needed for the local path.

## API example

```bash
curl -F "file=@notes.pdf" -F "subject=History" -F "exam_date=2026-12-10" http://127.0.0.1:8000/analyze
```

## Verify it

```bash
curl http://127.0.0.1:8000/
```

The response includes `"status": "ok"`.

## Limits

- Image input needs the Tesseract binary installed on the machine, not just the Python package.
- CORS allows all origins. Restrict it before any public deployment.
- `index.html` has a fixed API URL. Change `API_URL` there if the server runs elsewhere.
- Question quality follows the structure of your notes. Scanned handwriting will need a good OCR pass first.

## License

MIT. See [LICENSE](LICENSE).
