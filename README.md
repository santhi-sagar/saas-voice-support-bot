# Voxera — Independent Kapture CX Website Guide

Voice/text website-navigation demo for Kapture CX. Not affiliated with Kapture CX. Explains company information, products, careers/application routes, contact, demo requests, pricing guidance, support, offices, integrations, partnerships and security resources from reviewed official sources. No forms are submitted and no customer accounts are accessed.

Live browser app: https://saas-voice-support-bot.onrender.com

Read [KAPTURE_GUIDE.md](KAPTURE_GUIDE.md) for sources, scope and limitations. Read [PHONE_SETUP.md](PHONE_SETUP.md) for inbound caller activation. Phone activation must be verified separately; deployment alone does not mean a number is connected.

## Run

Install requirements.txt and run uvicorn app:app --host 127.0.0.1 --port 8765, or use START_VOXERA.bat. Keep VOXERA_ACCESS_CODE private. See LOCAL_RUN.md for local startup.

## Tests

uv run --no-project --with fastapi==0.115.6 --with httpx python test_phone.py

## Architecture

FastAPI backend, source-linked reviewed JSON knowledge pack, English browser speech recognition/synthesis, and optional signed Twilio inbound speech/DTMF webhooks. Uses deterministic topic routing, not a generative LLM or streaming speech model. Legacy SaaS articles are preserved but excluded from answers. Render free-tier sleep and SQLite restart-loss limitations remain. No audio recording or phone transcript storage by this app.
