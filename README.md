# Voxera — Multilingual Voice Support Bot

Voxera is a production-minded, free-to-run browser voice assistant for SaaS customer support. It supports English, Telugu, and Hindi, provides a browser microphone simulator, grounded answers from a local knowledge base, human handoff capture, conversation history, feedback, and an admin article area.

## What is included

- Browser speech recognition and speech synthesis with language switching: English (India), Telugu (India), Hindi (India)
- Responsive support console with voice, text, quick actions, confidence indicator, sources, feedback, and escalation
- FastAPI backend with SQLite persistence
- Grounded local answer engine that only answers from approved support articles
- Admin article creation and knowledge-base search
- Conversation logging, human handoff requests, CSAT feedback, and basic metrics
- Safety behavior: uncertainty fallback, no invented account/order data, and PII masking in logs
- Optional LLM adapter can be added later without changing the frontend contract
- Docker and Render deployment configuration

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Open http://localhost:8000. Microphone access works on localhost and HTTPS deployments. Use Chrome or Edge for the most reliable browser speech recognition.

## Deploy on Render free tier

1. Push this folder to a GitHub repository.
2. In Render, create a Web Service from the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Set `PYTHON_VERSION` to `3.11.9` if the platform asks for a runtime.
6. Open the HTTPS URL and allow microphone permission.

SQLite is suitable for a demo and low-volume pilot. For multi-agent production use, replace it with Postgres and add authenticated admin access before handling customer records.

## Design decisions

The browser uses the Web Speech API to keep the first deployment free. Speech recognition quality and availability vary by browser, so the text input remains a dependable fallback. The backend's local retrieval engine returns approved article snippets with confidence and a clear handoff path instead of fabricating answers.
