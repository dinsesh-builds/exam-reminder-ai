import re
from collections import Counter

def analyze_notes(text):
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

def find_definitions(text):
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

def find_comparisons(text):
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

def find_numbered_lists(text):
    items = re.findall(r"(?:^|\n)\s*(?:\d+\.|\([0-9]+\)|[0-9]\))\s+(.{10,100})", text)
    return [f"List with {len(items)} items: {items[0][:50]}..."] if len(items) >= 2 else []

def find_formulas(text):
    matches = re.findall(r"([A-Z][a-zA-Z]*\s*=\s*[^=\n]{2,50})", text)
    return list(set([m.strip() for m in matches if len(m) > 3]))[:10]

def find_bold_terms(text):
    bold = re.findall(r"\*\*([^*]{2,30})\*\*", text)
    under = re.findall(r"__([^_]{2,30})__", text)
    caps = re.findall(r"\b([A-Z]{3,15})\b", text)
    return list(set([t.strip() for t in bold + under + caps if len(t) > 2]))[:15]