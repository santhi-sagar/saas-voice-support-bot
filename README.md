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

## Permanent-free local run (recommended)

For a no-expiry, no-account, no-reverification deployment, run Voxera on your own Windows computer. Double-click `START_VOXERA.bat`. The first run performs a one-time local setup; later runs need no sign-in or cloud verification. It opens at http://127.0.0.1:8765.

See [LOCAL_RUN.md](LOCAL_RUN.md) for automatic startup, privacy, and availability details.

Manual setup is also available with Python 3.10+:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8765
```

Open http://127.0.0.1:8765. Microphone access works on localhost. Use Chrome or Edge for the most reliable browser speech recognition.

## Optional free cloud deployment

The included Render configuration is optional only. Free cloud providers can sleep, impose quotas, change policy, or require future verification. Use local mode when permanent free operation is a strict requirement.

## Deploy on Render free tier

1. Push this folder to a GitHub repository.
2. In Render, create a Web Service from the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Set `PYTHON_VERSION` to `3.11.9` if the platform asks for a runtime.
6. Open the HTTPS URL and allow microphone permission.

SQLite is suitable for a demo and low-volume pilot. For multi-agent production use, replace it with Postgres and add authenticated admin access before handling customer records.

## Accuracy and review controls

Voxera uses a grounded-or-escalate policy. It searches only approved support articles, requires a 0.65 confidence threshold, shows the approved article title and version, and escalates when no reliable match exists. It does not invent account, payment, order, or policy details.

New articles are marked `pending_review` and cannot answer customers. A reviewer can approve or reject them from the Admin panel. Each edit creates an immutable article version with a change note, reviewer timestamp, status, and optional Telugu/Hindi answer variants. Only the approved version is searchable.

The seeded guides include approved English, Telugu, and Hindi responses. The text field remains available as a fallback because browser speech recognition quality varies by browser.

## Design decisions

The browser uses the Web Speech API to keep the first deployment free. Speech recognition quality and availability vary by browser, so the text input remains a dependable fallback. The backend's local retrieval engine returns approved article snippets with confidence and a clear handoff path instead of fabricating answers.
