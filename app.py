from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).parent
DATA = BASE / "data"
DB_PATH = Path(os.getenv("VOXERA_DB", str(DATA / "voxera.db")))
KNOWLEDGE_PATH = DATA / "knowledge.json"

app = FastAPI(title="Voxera Voice Support API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SUPPORTED_LANGUAGES = {"en-IN": "English", "te-IN": "Telugu", "hi-IN": "Hindi"}
TRANSLATIONS = {
    "en-IN": {
        "greeting": "Hello. I am Voxera, your support assistant. How can I help?",
        "fallback": "I want to make sure I give you an accurate answer. I could not find that in the approved support guide. Would you like me to connect you with a human specialist?",
        "handoff": "I have recorded your request for a human specialist. A support team member can follow up by email.",
    },
    "te-IN": {
        "greeting": "నమస్కారం. నేను వోక్సెరా సపోర్ట్ అసిస్టెంట్‌ను. నేను ఎలా సహాయం చేయగలను?",
        "fallback": "ఖచ్చితమైన సమాధానం ఇవ్వడానికి, ఆ ప్రశ్నకు మా సపోర్ట్ గైడ్‌లో సమాచారం దొరకలేదు. మానవ సపోర్ట్ నిపుణుడితో మాట్లాడాలా?",
        "handoff": "మానవ సపోర్ట్ నిపుణుడి కోసం మీ అభ్యర్థనను నమోదు చేశాను. సపోర్ట్ టీమ్ ఇమెయిల్ ద్వారా సంప్రదిస్తుంది.",
    },
    "hi-IN": {
        "greeting": "नमस्ते। मैं वोक्सेरा सपोर्ट असिस्टेंट हूं। मैं आपकी कैसे मदद कर सकता हूं?",
        "fallback": "सही उत्तर देने के लिए, मुझे स्वीकृत सपोर्ट गाइड में इस प्रश्न की जानकारी नहीं मिली। क्या आप किसी मानव विशेषज्ञ से जुड़ना चाहेंगे?",
        "handoff": "मैंने मानव सपोर्ट विशेषज्ञ के लिए आपका अनुरोध दर्ज कर लिया है। सपोर्ट टीम ईमेल से संपर्क करेगी।",
    },
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "en-IN"
    conversation_id: str | None = None


class FeedbackRequest(BaseModel):
    conversation_id: str
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)


class HandoffRequest(BaseModel):
    conversation_id: str | None = None
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=200)
    issue: str = Field(min_length=1, max_length=2000)
    language: str = "en-IN"


class ArticleRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    category: str = Field(min_length=2, max_length=80)
    content: str = Field(min_length=10, max_length=4000)
    keywords: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)


def db() -> sqlite3.Connection:
    DATA.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS articles (id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, keywords TEXT NOT NULL, content TEXT NOT NULL, steps TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, message TEXT NOT NULL, response TEXT NOT NULL, language TEXT NOT NULL, confidence REAL NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS handoffs (id TEXT PRIMARY KEY, conversation_id TEXT, name TEXT NOT NULL, email TEXT NOT NULL, issue TEXT NOT NULL, language TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
            """
        )
        count = con.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
        if count == 0 and KNOWLEDGE_PATH.exists():
            seed = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
            for article in seed:
                con.execute(
                    "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        article["title"],
                        article["category"],
                        json.dumps(article["keywords"]),
                        article["content"],
                        json.dumps(article.get("steps", [])),
                        now(),
                    ),
                )


def mask_pii(text: str) -> str:
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", text)
    return re.sub(r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b", "[phone]", text)


STOPWORDS = {
    "the", "and", "for", "how", "what", "can", "could", "would", "you", "your",
    "my", "from", "this", "that", "with", "need", "want", "please", "help", "tell",
    "about", "does", "where", "when", "yesterday", "today", "there", "have", "has",
}


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\w]+", text.lower()) if len(t) > 2 and t not in STOPWORDS}


def retrieve(message: str) -> tuple[sqlite3.Row | None, float]:
    query = tokens(message)
    if not query:
        return None, 0.0
    with db() as con:
        rows = con.execute("SELECT * FROM articles").fetchall()
    best, best_score = None, 0.0
    for row in rows:
        haystack = " ".join([row["title"], row["category"], row["content"], row["keywords"]])
        article_tokens = tokens(haystack)
        overlap = len(query & article_tokens)
        # Require two meaningful matches before an article can be trusted. This avoids
        # answering a refund/account-specific question from a generic word like payment.
        if overlap < 2:
            continue
        phrase_bonus = 0.15 if any(k.lower() in message.lower() for k in json.loads(row["keywords"])) else 0
        score = min(0.99, (overlap / max(len(query), 1)) * 0.75 + phrase_bonus)
        if score > best_score:
            best, best_score = row, score
    return best, round(best_score, 2)


def response_for(message: str, language: str) -> tuple[str, float, str, dict[str, Any] | None]:
    language = language if language in SUPPORTED_LANGUAGES else "en-IN"
    article, confidence = retrieve(message)
    if article and confidence >= 0.28:
        intro = {
            "en-IN": "Here is what I found:",
            "te-IN": "ఇది నాకు దొరికిన సమాచారం:",
            "hi-IN": "मुझे यह जानकारी मिली:",
        }[language]
        answer = f"{intro} {article['content']}"
        return answer, confidence, "knowledge_base", {"title": article["title"], "category": article["category"], "steps": json.loads(article["steps"])}
    return TRANSLATIONS[language]["fallback"], confidence, "safe_fallback", None


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, Any]:
    with db() as con:
        articles = con.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
    return {"status": "ok", "service": "voxera", "articles": articles, "languages": SUPPORTED_LANGUAGES}


@app.get("/api/greeting")
def greeting(language: str = "en-IN") -> dict[str, str]:
    language = language if language in SUPPORTED_LANGUAGES else "en-IN"
    return {"message": TRANSLATIONS[language]["greeting"], "language": language}


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    language = payload.language if payload.language in SUPPORTED_LANGUAGES else "en-IN"
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    answer, confidence, source, citation = response_for(payload.message, language)
    with db() as con:
        con.execute(
            "INSERT INTO conversations VALUES (?, ?, ?, ?, ?, ?, ?)",
            (conversation_id, mask_pii(payload.message), mask_pii(answer), language, confidence, source, now()),
        )
    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "language": language,
        "confidence": confidence,
        "source": source,
        "citation": citation,
        "needs_handoff": source == "safe_fallback",
    }


@app.post("/api/feedback")
def feedback(payload: FeedbackRequest) -> dict[str, str]:
    with db() as con:
        con.execute(
            "INSERT INTO feedback VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), payload.conversation_id, payload.rating, mask_pii(payload.comment), now()),
        )
    return {"status": "recorded"}


@app.post("/api/handoff")
def handoff(payload: HandoffRequest) -> dict[str, Any]:
    language = payload.language if payload.language in SUPPORTED_LANGUAGES else "en-IN"
    with db() as con:
        handoff_id = str(uuid.uuid4())
        con.execute(
            "INSERT INTO handoffs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (handoff_id, payload.conversation_id, mask_pii(payload.name), mask_pii(payload.email), mask_pii(payload.issue), language, "new", now()),
        )
    return {"status": "received", "handoff_id": handoff_id, "message": TRANSLATIONS[language]["handoff"]}


@app.get("/api/articles")
def articles(q: str = "") -> list[dict[str, Any]]:
    with db() as con:
        rows = con.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["keywords"] = json.loads(item["keywords"])
        item["steps"] = json.loads(item["steps"])
        if not q or q.lower() in json.dumps(item).lower():
            result.append(item)
    return result


@app.post("/api/articles")
def create_article(payload: ArticleRequest) -> dict[str, Any]:
    item = (
        str(uuid.uuid4()),
        payload.title,
        payload.category,
        json.dumps(payload.keywords),
        payload.content,
        json.dumps(payload.steps),
        now(),
    )
    with db() as con:
        con.execute("INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)", item)
    return {"status": "created", "id": item[0]}


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    with db() as con:
        conversations = con.execute("SELECT COUNT(*) AS n FROM conversations").fetchone()["n"]
        handoffs = con.execute("SELECT COUNT(*) AS n FROM handoffs").fetchone()["n"]
        avg = con.execute("SELECT AVG(rating) AS value FROM feedback").fetchone()["value"]
        articles_count = con.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
    return {"conversations": conversations, "handoffs": handoffs, "average_rating": round(avg, 2) if avg else None, "articles": articles_count}


app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(BASE / "static" / "index.html")
