from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).parent
DATA = BASE / "data"
DB_PATH = Path(os.getenv("VOXERA_DB", str(DATA / "voxera.db")))
KNOWLEDGE_PATH = DATA / "knowledge.json"
ACCESS_CODE_PATH = DATA / "access_code.txt"

app = FastAPI(title="Voxera Voice Support API", version="1.0.0")


def access_code() -> str:
    configured = os.getenv("VOXERA_ACCESS_CODE", "").strip()
    if configured:
        return configured
    DATA.mkdir(exist_ok=True)
    if ACCESS_CODE_PATH.exists():
        return ACCESS_CODE_PATH.read_text(encoding="utf-8").strip()
    generated = secrets.token_urlsafe(9)
    ACCESS_CODE_PATH.write_text(generated, encoding="utf-8")
    print("Voxera access code generated. Keep data/access_code.txt private.")
    return generated


def token_for(code: str) -> str:
    return hmac.new(access_code().encode(), code.encode(), hashlib.sha256).hexdigest()


def require_access(request: Request) -> None:
    provided = request.headers.get("X-Access-Token", "")
    if not provided or not hmac.compare_digest(provided, token_for(access_code())):
        raise HTTPException(status_code=401, detail="Valid Voxera access code required")
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
    translations: dict[str, dict[str, Any]] = Field(default_factory=dict)
    change_note: str = Field(default="", max_length=500)


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = Field(default="", max_length=1000)


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
            CREATE TABLE IF NOT EXISTS articles (id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, keywords TEXT NOT NULL, content TEXT NOT NULL, steps TEXT NOT NULL, created_at TEXT NOT NULL, translations TEXT NOT NULL DEFAULT '{}', version INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'approved', change_note TEXT NOT NULL DEFAULT '', reviewed_at TEXT);
            CREATE TABLE IF NOT EXISTS article_versions (id TEXT PRIMARY KEY, article_id TEXT NOT NULL, version INTEGER NOT NULL, title TEXT NOT NULL, category TEXT NOT NULL, keywords TEXT NOT NULL, content TEXT NOT NULL, steps TEXT NOT NULL, translations TEXT NOT NULL, status TEXT NOT NULL, change_note TEXT NOT NULL, created_at TEXT NOT NULL, reviewed_at TEXT);
            CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, message TEXT NOT NULL, response TEXT NOT NULL, language TEXT NOT NULL, confidence REAL NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS handoffs (id TEXT PRIMARY KEY, conversation_id TEXT, name TEXT NOT NULL, email TEXT NOT NULL, issue TEXT NOT NULL, language TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
            """
        )
        existing_columns = {row[1] for row in con.execute("PRAGMA table_info(articles)").fetchall()}
        migrations = {
            "translations": "TEXT NOT NULL DEFAULT '{}'",
            "version": "INTEGER NOT NULL DEFAULT 1",
            "status": "TEXT NOT NULL DEFAULT 'approved'",
            "change_note": "TEXT NOT NULL DEFAULT ''",
            "reviewed_at": "TEXT",
        }
        for column, definition in migrations.items():
            if column not in existing_columns:
                con.execute(f"ALTER TABLE articles ADD COLUMN {column} {definition}")
        count = con.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
        if count == 0 and KNOWLEDGE_PATH.exists():
            seed = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
            for article in seed:
                article_id = str(uuid.uuid4())
                created = now()
                translations = article.get("translations", {})
                con.execute(
                    "INSERT INTO articles (id,title,category,keywords,content,steps,created_at,translations,version,status,change_note,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (article_id, article["title"], article["category"], json.dumps(article["keywords"]), article["content"], json.dumps(article.get("steps", [])), created, json.dumps(translations, ensure_ascii=False), 1, "approved", "Seeded approved support guide", created),
                )
                con.execute(
                    "INSERT INTO article_versions (id,article_id,version,title,category,keywords,content,steps,translations,status,change_note,created_at,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), article_id, 1, article["title"], article["category"], json.dumps(article["keywords"]), article["content"], json.dumps(article.get("steps", [])), json.dumps(translations, ensure_ascii=False), "approved", "Seeded approved support guide", created, created),
                )
        if KNOWLEDGE_PATH.exists():
            for article in json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8")):
                current = con.execute("SELECT * FROM articles WHERE title = ?", (article["title"],)).fetchone()
                if not current:
                    article_id = str(uuid.uuid4())
                    created = now()
                    translations = article.get("translations", {})
                    con.execute("INSERT INTO articles (id,title,category,keywords,content,steps,created_at,translations,version,status,change_note,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (article_id, article["title"], article["category"], json.dumps(article["keywords"]), article["content"], json.dumps(article.get("steps", [])), created, json.dumps(translations, ensure_ascii=False), 1, "approved", "Seeded approved support guide", created))
                    con.execute("INSERT INTO article_versions (id,article_id,version,title,category,keywords,content,steps,translations,status,change_note,created_at,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), article_id, 1, article["title"], article["category"], json.dumps(article["keywords"]), article["content"], json.dumps(article.get("steps", [])), json.dumps(translations, ensure_ascii=False), "approved", "Seeded approved support guide", created, created))
                    continue
                if not current["translations"] or current["translations"] == "{}":
                    translations = json.dumps(article.get("translations", {}), ensure_ascii=False)
                    con.execute("UPDATE articles SET translations=? WHERE id=?", (translations, current["id"]))
                    version_exists = con.execute("SELECT COUNT(*) AS n FROM article_versions WHERE article_id=?", (current["id"],)).fetchone()["n"]
                    if not version_exists:
                        con.execute("INSERT INTO article_versions (id,article_id,version,title,category,keywords,content,steps,translations,status,change_note,created_at,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), current["id"], current["version"], current["title"], current["category"], current["keywords"], current["content"], current["steps"], translations, current["status"], "Backfilled approved translations", current["created_at"], current["reviewed_at"]))


def mask_pii(text: str) -> str:
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", text)
    return re.sub(r"\b(?:\+?91[- ]?)?[6-9]\d{9}\b", "[phone]", text)


STOPWORDS = {
    "the", "and", "for", "how", "what", "can", "could", "would", "you", "your",
    "my", "from", "this", "that", "with", "need", "want", "please", "help", "tell",
    "about", "does", "where", "when", "yesterday", "today", "there", "have", "has",
    "is", "are", "was", "were", "did", "why", "do", "right", "now",
}


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\w]+", text.lower()) if len(t) > 2 and t not in STOPWORDS}


def retrieve(message: str) -> tuple[sqlite3.Row | None, float]:
    query = tokens(message)
    if not query:
        return None, 0.0
    with db() as con:
        rows = con.execute("SELECT * FROM articles WHERE status = 'approved'").fetchall()
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


ANSWER_THRESHOLD = 0.65


def response_for(message: str, language: str) -> tuple[str, float, str, dict[str, Any] | None]:
    language = language if language in SUPPORTED_LANGUAGES else "en-IN"
    article, confidence = retrieve(message)
    if article and confidence >= ANSWER_THRESHOLD:
        translations = json.loads(article["translations"] or "{}")
        localized = translations.get(language, {})
        intro = {
            "en-IN": "Here is what I found:",
            "te-IN": "ఇది నాకు దొరికిన సమాచారం:",
            "hi-IN": "मुझे यह जानकारी मिली:",
        }[language]
        answer = f"{intro} {localized.get('content', article['content'])}"
        steps = localized.get("steps", json.loads(article["steps"]))
        return answer, confidence, "knowledge_base", {"title": article["title"], "category": article["category"], "steps": steps, "version": article["version"], "reviewed_at": article["reviewed_at"]}
    return TRANSLATIONS[language]["fallback"], confidence, "safe_fallback", {"threshold": ANSWER_THRESHOLD, "reason": "No approved article met the confidence threshold"}


@app.on_event("startup")
def startup() -> None:
    init_db()
    access_code()


@app.get("/api/health")
def health() -> dict[str, Any]:
    with db() as con:
        articles = con.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
    with db() as con:
        pending = con.execute("SELECT COUNT(*) AS n FROM articles WHERE status = 'pending_review'").fetchone()["n"]
    return {"status": "ok", "service": "voxera", "articles": articles, "pending_review": pending, "answer_threshold": ANSWER_THRESHOLD, "languages": SUPPORTED_LANGUAGES}


@app.post("/api/auth/login")
def login(payload: dict[str, str]) -> dict[str, Any]:
    supplied = str(payload.get("access_code", "")).strip()
    if not supplied or not hmac.compare_digest(supplied, access_code()):
        raise HTTPException(status_code=401, detail="Invalid access code")
    return {"status": "authenticated", "token": token_for(supplied)}


@app.get("/api/auth/status")
def auth_status(request: Request) -> dict[str, str]:
    require_access(request)
    return {"status": "authenticated"}


@app.get("/api/greeting")
def greeting(language: str = "en-IN") -> dict[str, str]:
    language = language if language in SUPPORTED_LANGUAGES else "en-IN"
    return {"message": TRANSLATIONS[language]["greeting"], "language": language}


@app.post("/api/chat")
def chat(payload: ChatRequest, request: Request) -> dict[str, Any]:
    require_access(request)
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
def feedback(payload: FeedbackRequest, request: Request) -> dict[str, str]:
    require_access(request)
    with db() as con:
        con.execute(
            "INSERT INTO feedback VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), payload.conversation_id, payload.rating, mask_pii(payload.comment), now()),
        )
    return {"status": "recorded"}


@app.post("/api/handoff")
def handoff(payload: HandoffRequest, request: Request) -> dict[str, Any]:
    require_access(request)
    language = payload.language if payload.language in SUPPORTED_LANGUAGES else "en-IN"
    with db() as con:
        handoff_id = str(uuid.uuid4())
        con.execute(
            "INSERT INTO handoffs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (handoff_id, payload.conversation_id, mask_pii(payload.name), mask_pii(payload.email), mask_pii(payload.issue), language, "new", now()),
        )
    return {"status": "received", "handoff_id": handoff_id, "message": TRANSLATIONS[language]["handoff"]}


@app.get("/api/articles")
def articles(request: Request, q: str = "") -> list[dict[str, Any]]:
    require_access(request)
    with db() as con:
        rows = con.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["keywords"] = json.loads(item["keywords"])
        item["steps"] = json.loads(item["steps"])
        item["translations"] = json.loads(item.get("translations") or "{}")
        if not q or q.lower() in json.dumps(item, ensure_ascii=False).lower():
            result.append(item)
    return result


@app.post("/api/articles")
def create_article(payload: ArticleRequest, request: Request) -> dict[str, Any]:
    require_access(request)
    article_id, created = str(uuid.uuid4()), now()
    translations = json.dumps(payload.translations, ensure_ascii=False)
    with db() as con:
        con.execute(
            "INSERT INTO articles (id,title,category,keywords,content,steps,created_at,translations,version,status,change_note,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (article_id, payload.title, payload.category, json.dumps(payload.keywords), payload.content, json.dumps(payload.steps), created, translations, 1, "pending_review", payload.change_note, None),
        )
        con.execute(
            "INSERT INTO article_versions (id,article_id,version,title,category,keywords,content,steps,translations,status,change_note,created_at,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), article_id, 1, payload.title, payload.category, json.dumps(payload.keywords), payload.content, json.dumps(payload.steps), translations, "pending_review", payload.change_note, created, None),
        )
    return {"status": "pending_review", "id": article_id, "version": 1}


@app.put("/api/articles/{article_id}")
def update_article(article_id: str, payload: ArticleRequest, request: Request) -> dict[str, Any]:
    require_access(request)
    created = now()
    translations = json.dumps(payload.translations, ensure_ascii=False)
    with db() as con:
        current = con.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Article not found")
        version = int(current["version"]) + 1
        con.execute(
            "UPDATE articles SET title=?, category=?, keywords=?, content=?, steps=?, translations=?, version=?, status='pending_review', change_note=?, reviewed_at=NULL WHERE id=?",
            (payload.title, payload.category, json.dumps(payload.keywords), payload.content, json.dumps(payload.steps), translations, version, payload.change_note, article_id),
        )
        con.execute(
            "INSERT INTO article_versions (id,article_id,version,title,category,keywords,content,steps,translations,status,change_note,created_at,reviewed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), article_id, version, payload.title, payload.category, json.dumps(payload.keywords), payload.content, json.dumps(payload.steps), translations, "pending_review", payload.change_note, created, None),
        )
    return {"status": "pending_review", "id": article_id, "version": version}


@app.post("/api/articles/{article_id}/review")
def review_article(article_id: str, payload: ReviewRequest, request: Request) -> dict[str, Any]:
    require_access(request)
    reviewed = now()
    with db() as con:
        current = con.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Article not found")
        status = "approved" if payload.decision == "approve" else "rejected"
        con.execute("UPDATE articles SET status=?, reviewed_at=? WHERE id=?", (status, reviewed, article_id))
        con.execute("UPDATE article_versions SET status=?, reviewed_at=? WHERE article_id=? AND version=?", (status, reviewed, article_id, current["version"]))
    return {"status": status, "id": article_id, "version": current["version"], "note": payload.note}


@app.get("/api/articles/{article_id}/versions")
def article_versions(article_id: str, request: Request) -> list[dict[str, Any]]:
    require_access(request)
    with db() as con:
        rows = con.execute("SELECT * FROM article_versions WHERE article_id=? ORDER BY version DESC", (article_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for field in ("keywords", "steps", "translations"):
            item[field] = json.loads(item[field])
        result.append(item)
    return result


@app.get("/api/metrics")
def metrics(request: Request) -> dict[str, Any]:
    require_access(request)
    with db() as con:
        conversations = con.execute("SELECT COUNT(*) AS n FROM conversations").fetchone()["n"]
        handoffs = con.execute("SELECT COUNT(*) AS n FROM handoffs").fetchone()["n"]
        avg = con.execute("SELECT AVG(rating) AS value FROM feedback").fetchone()["value"]
        articles_count = con.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
        pending = con.execute("SELECT COUNT(*) AS n FROM articles WHERE status = 'pending_review'").fetchone()["n"]
        versions = con.execute("SELECT COUNT(*) AS n FROM article_versions").fetchone()["n"]
    return {"conversations": conversations, "handoffs": handoffs, "average_rating": round(avg, 2) if avg else None, "articles": articles_count, "pending_review": pending, "versions": versions, "answer_threshold": ANSWER_THRESHOLD}


app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(BASE / "static" / "index.html")
