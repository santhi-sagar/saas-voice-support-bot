# Voxera — Kapture CX Website Guide + HR Practice Demo

Live browser app: https://saas-voice-support-bot.onrender.com
Repository: https://github.com/santhi-sagar/saas-voice-support-bot

Voxera is an independent Kapture CX public-website guide, not a Kapture service. It answers from a reviewed official-site guide and links source pages. A separate English/Hindi browser-only mock interview lets users rehearse role, education, relevant experience, skills/projects, and preferred interview windows. It asks users to use synthetic details, keeps answers in the page only, sends/stores none in this app, and does not score applicants, check calendars, book slots, or contact candidates. Browser speech recognition may process audio through the browser/provider service.

Read [KAPTURE_GUIDE.md](KAPTURE_GUIDE.md), [HR_SIMULATION.md](HR_SIMULATION.md), and [PHONE_SETUP.md](PHONE_SETUP.md). The inbound phone module is a Kapture FAQ demo in English and Hindi with a caller language choice; current production readiness and number activation must be separately verified. Outbound candidate calling is not implemented or enabled. No number may be purchased and no call placed without separate approval.

## Run and test

Install requirements.txt, then run `uvicorn app:app --host 127.0.0.1 --port 8765` or use START_VOXERA.bat. Keep VOXERA_ACCESS_CODE private. Tests: `uv run --no-project --with fastapi==0.115.6 --with httpx python test_phone.py`; syntax: `node --check static/app.js` and `node --check static/hr-simulation.js`.

## Architecture and limitations

FastAPI backend, source-linked Kapture JSON guide, browser speech recognition/synthesis, and optional signed Twilio inbound speech/DTMF FAQ. Grounded topic matching is deterministic; this is not an autonomous recruiter or streaming LLM. Legacy SaaS articles remain preserved but excluded from public Kapture answers. Free-tier Render sleep and restart/persistence limitations apply. The HR mock interview has no API endpoint, calendar integration, persistence, evaluation, or hiring decision.
