import os
import re
from collections import Counter
from datetime import datetime, date, timedelta

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ocr_service import extract_text

app = FastAPI(title="Exam Reminder", version="2.0")

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
MAGIC = {
    ".pdf": b"%PDF",
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".bmp": b"BM",
    ".tiff": (b"II*\x00", b"MM\x00*"),
}

origins = os.getenv("EXAM_ALLOWED_ORIGINS")
allow_origins = origins.split(",") if origins else ["null", "http://127.0.0.1:8000", "http://localhost:8000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


def validate_upload(filename: str, contents: bytes) -> None:
    extension = os.path.splitext(filename.lower())[1]
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use txt, pdf, png, jpg, jpeg, bmp or tiff.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 10 MB.")
    expected = MAGIC.get(extension)
    if expected and not contents.startswith(expected):
        raise HTTPException(status_code=400, detail="File content does not match its extension.")

def parse_date(date_str: str):
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date '{date_str}' not recognized. Use YYYY-MM-DD format.")

def analyze_notes(text: str) -> dict:
    words = text.split()
    nouns = [w.lower().strip(".,;()") for w in words if w[0].isupper() and len(w) > 3]
    freq = Counter(nouns)
    top = freq.most_common(10)
    
    return {
        "definitions": find_definitions(text),
        "comparisons": find_comparisons(text),
        "lists": find_numbered_lists(text),
        "formulas": find_formulas(text),
        "bold_terms": find_bold_terms(text),
        "top_topics": [{"topic": w, "mentions": c} for w, c in top],
        "total_words": len(words),
    }

def find_definitions(text: str) -> list:
    patterns = [
        r"(?:definition of|define)\s+([A-Z][a-zA-Z\s]{2,30})",
        r"([A-Z][a-zA-Z\s]{2,30})\s+is defined as",
        r"([A-Z][a-zA-Z\s]{2,30})\s+refers to",
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        found.extend([m.strip() for m in matches if len(m.strip()) > 3])
    return list(set(found))[:10]

def find_comparisons(text: str) -> list:
    patterns = [
        r"([A-Z][a-zA-Z]+)\s+(?:vs|versus|vs\.)\s+([A-Z][a-zA-Z]+)",
        r"difference between\s+([A-Z][a-zA-Z\s]+)\s+and\s+([A-Z][a-zA-Z\s]+)",
        r"compare\s+([A-Z][a-zA-Z\s]+)\s+(?:with|and|to)\s+([A-Z][a-zA-Z\s]+)",
    ]
    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                found.append(f"{m[0].strip()} vs {m[1].strip()}")
            else:
                found.append(m.strip())
    return list(set(found))[:10]

def find_numbered_lists(text: str) -> list:
    items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\([0-9]+\)|[0-9]\))\s+(.{10,100})", text)
    return [f"List with {len(items)} items: {items[0][:50]}..."] if len(items) >= 2 else []

def find_formulas(text: str) -> list:
    matches = re.findall(r"([A-Z][a-zA-Z]*\s*=\s*[^=\n]{2,50})", text)
    return list(set([m.strip() for m in matches if len(m) > 3]))[:10]

def find_bold_terms(text: str) -> list:
    bold = re.findall(r"\*\*([^*]{2,30})\*\*", text)
    under = re.findall(r"__([^_]{2,30})__", text)
    caps = re.findall(r"\b([A-Z]{3,15})\b", text)
    return list(set([t.strip() for t in bold + under + caps if len(t) > 2]))[:15]

def answer_from_source(term: str, source_text: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", source_text):
        if term and term.lower() in sentence.lower():
            return sentence.strip()[:240]
    return term


def bloom_level(question: str) -> str:
    text = question.lower()
    if any(word in text for word in ("define", "list", "state", "name", "what is")):
        return "Remember"
    if any(word in text for word in ("differentiate", "compare", "infer", "analyze")):
        return "Analyze"
    if any(word in text for word in ("formula", "numerical")):
        return "Apply"
    return "Understand"


def generate_questions(analysis: dict, subject: str, source_text: str = "") -> list:
    """Generate questions directly from analysis without external API."""
    questions = []
    
    # Definition questions
    for i, def_term in enumerate(analysis.get("definitions", [])[:3]):
        clean_term = def_term.replace("\r", "").replace("\n", " ").strip()[:50]
        questions.append({
            "question": f"Define {clean_term}.",
            "topic": clean_term,
            "type": "definition",
            "difficulty": "Easy",
            "marks": 2,
            "why_important": "Found as definition in notes",
            "source": clean_term
        })
    
    # Comparison questions
    for i, comp in enumerate(analysis.get("comparisons", [])[:2]):
        questions.append({
            "question": f"Differentiate between {comp}.",
            "topic": comp,
            "type": "comparison",
            "difficulty": "Medium",
            "marks": 5,
            "why_important": "Comparison found in notes",
            "source": comp
        })
    
    # Short answer from topics
    for i, topic in enumerate(analysis.get("top_topics", [])[:3]):
        questions.append({
            "question": f"Explain {topic['topic']} in detail.",
            "topic": topic['topic'],
            "type": "short",
            "difficulty": "Medium",
            "marks": 5,
            "why_important": f"Mentioned {topic['mentions']} times in notes",
            "source": topic['topic']
        })
    
    # Long answer from top topic
    if analysis.get("top_topics"):
        top = analysis["top_topics"][0]["topic"]
        questions.append({
            "question": f"Describe {top} with examples and diagrams.",
            "topic": top,
            "type": "long",
            "difficulty": "Hard",
            "marks": 10,
            "why_important": "Most frequently mentioned topic",
            "source": top
        })
    
    # List/process questions
    for i, lst in enumerate(analysis.get("lists", [])[:2]):
        questions.append({
            "question": f"Explain the following process: {lst}",
            "topic": "process",
            "type": "short",
            "difficulty": "Medium",
            "marks": 5,
            "why_important": "Numbered list found in notes",
            "source": lst[:80]
        })
    
    # Formula questions
    for i, formula in enumerate(analysis.get("formulas", [])[:2]):
        questions.append({
            "question": f"Explain the formula: {formula}",
            "topic": "formula",
            "type": "numerical",
            "difficulty": "Medium",
            "marks": 5,
            "why_important": "Formula found in notes",
            "source": formula
        })
    
    for question in questions:
        question["answer"] = answer_from_source(question["source"], source_text)
        question["bloom"] = bloom_level(question["question"])

    if source_text:
        haystack = source_text.lower()
        questions = [q for q in questions if q["answer"].strip() and q["answer"].lower() in haystack]

    return questions

@app.get("/")
def root():
    return {"message": "Exam Reminder is running", "status": "ok"}

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    subject: str = Form("General"),
    exam_date: str = Form(None)
):
    if file.size and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 10 MB.")
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 10 MB.")
    validate_upload(file.filename or "uploaded_file", contents)
    try:
        raw_text = extract_text(contents, file.filename or "uploaded_file")
    except ValueError:
        raise HTTPException(status_code=400, detail="Could not read text from that file.")
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in that file. Try a text based PDF or a clear image.")
    analysis = analyze_notes(raw_text)

    days_remaining = None
    if exam_date:
        try:
            exam = parse_date(exam_date)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        days_remaining = (exam - date.today()).days

    questions = generate_questions(analysis, subject, raw_text)
    
    schedule = []
    if days_remaining and days_remaining > 0:
        topics = [t["topic"] for t in analysis.get("top_topics", [])]
        if topics:
            for day in range(1, min(days_remaining + 1, 14)):
                start_idx = (day - 1) * max(1, len(topics) // max(days_remaining, 1))
                end_idx = start_idx + max(1, len(topics) // max(days_remaining, 1))
                day_topics = topics[start_idx:end_idx] if start_idx < len(topics) else ["Review"]
                schedule.append({
                    "day": day,
                    "date": str(date.today() + timedelta(days=day-1)),
                    "topics": day_topics,
                    "urgency": "high" if day <= 2 else "medium" if day <= 5 else "low"
                })
    
    return {
        "filename": file.filename,
        "subject": subject,
        "exam_date": exam_date,
        "days_remaining": days_remaining,
        "analysis": analysis,
        "questions": questions,
        "study_schedule": schedule
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)