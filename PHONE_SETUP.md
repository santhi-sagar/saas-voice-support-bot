# Voxera inbound phone support — FlowDesk demo

FlowDesk is a fictional SaaS product. The existing approved SaaS support articles form its demo knowledge base; these are not policies of any real company. This implementation uses grounded local retrieval, not a generative LLM or a streaming real-time speech model.

## What works in the implementation

- Inbound Twilio HTTPS webhook with provider signature and account validation.
- Turn-by-turn English (India) speech recognition and text-to-speech.
- Keypad 1: sign-in; 2: invoices; 3: cancellation; 9: human-support information; 0: hang up.
- Explicit AI and fictional-product disclosure. No audio recording by this application.
- Approved-article answers, unsupported-question fallback, no fabricated account access or live transfer.
- Two empty responses end the call; 12 turns cap the demo flow.
- Phone conversation transcripts and caller numbers are not saved by this implementation. Twilio may retain provider call metadata under its own settings.

## Secure Render environment configuration

Set these in Render's Environment panel, never in GitHub or chat:

- VOXERA_PUBLIC_URL = https://saas-voice-support-bot.onrender.com
- TWILIO_ACCOUNT_SID = the account SID from your Twilio account
- TWILIO_AUTH_TOKEN = the account Auth Token (not an API key secret)

Keep the existing VOXERA_ACCESS_CODE unchanged. /api/voice/readiness reports configuration presence only, not proof that a number or live call works.

## Twilio number configuration

On an existing voice-enabled number, set 'A call comes in' to Webhook, HTTP POST:
https://saas-voice-support-bot.onrender.com/api/voice/incoming

Do not use the browser access code on the phone webhook. Twilio signatures authorize requests.

Do not buy or provision a number, upgrade billing, or place an outbound test call without the account owner's explicit approval. Trial-account limitations and available numbers must be checked in the console before activation. Caller-carrier charges may apply, especially for international dialing.

## Testing

uv run --no-project --with fastapi==0.115.6 --with httpx python test_phone.py

The 10 regression tests cover intro, health, keypad, hangup, no fake transfer, silence/turn limits, invalid signatures/accounts, and XML escaping. Tests use fake credentials only.

## Required live acceptance

1. Confirm Render deployment completed successfully and the existing browser app still works.
2. Securely configure the environment above.
3. Confirm a voice-enabled number exists and save its inbound webhook.
4. The owner calls the number and verifies greeting, a supported question, an unsupported question, keypad controls, silence timeout, and hangup.
5. Mark caller-ready only after a successful real call.

Render free-tier cold starts can delay inbound webhooks. This is a trial/demo, not a guaranteed always-on production line. English phone support only in this version; the existing browser supports English, Telugu, and Hindi. Live human transfer, generative LLM conversation, durable call analytics, and authenticated account actions are not implemented.
