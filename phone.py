"""Inbound Twilio speech/DTMF support. No outbound calling or recording."""
import base64
import hashlib
import hmac
import os
import re
from urllib.parse import urlencode, parse_qs
from xml.etree.ElementTree import Element, SubElement, tostring

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

router = APIRouter(prefix="/api/voice")
PRODUCT = "Kapture CX website guide"


def configured():
    base = os.getenv("VOXERA_PUBLIC_URL", "").rstrip("/")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    return base, token, sid


async def verified_form(request):
    base, token, sid = configured()
    if not base.startswith("https://") or not token or not sid:
        raise HTTPException(503, "Phone service is not configured")
    raw = await request.body()
    if len(raw) > 16000:
        raise HTTPException(413, "Payload too large")
    parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    if any(len(v) != 1 for v in parsed.values()):
        raise HTTPException(400, "Duplicate parameters are not accepted")
    form = {k: v[0] for k, v in parsed.items()}
    url = base + request.url.path
    if request.url.query:
        url += "?" + request.url.query
    message = url + "".join(k + form[k] for k in sorted(form))
    expected = base64.b64encode(hmac.new(token.encode(), message.encode(), hashlib.sha1).digest()).decode()
    if not hmac.compare_digest(request.headers.get("X-Twilio-Signature", ""), expected):
        raise HTTPException(403, "Invalid provider signature")
    if form.get("AccountSid") != sid or not re.fullmatch(r"CA[0-9a-fA-F]{32}", form.get("CallSid", "")):
        raise HTTPException(403, "Unexpected account or call")
    return form


def xml_response(root):
    return Response(tostring(root, encoding="unicode"), media_type="application/xml")


def say(root, text):
    SubElement(root, "Say", {"language": "en-IN"}).text = text


def gather(root, prompt, turn=0, empty=0):
    base, _, _ = configured()
    action = base + "/api/voice/turn?" + urlencode({"turn": turn, "empty": empty})
    node = SubElement(root, "Gather", {"input": "speech dtmf", "numDigits": "1", "language": "en-IN", "speechTimeout": "auto", "timeout": "6", "actionOnEmptyResult": "true", "action": action, "method": "POST"})
    say(node, prompt)
    return root


@router.get("/readiness")
def readiness():
    base, token, sid = configured()
    return {"configured": bool(base.startswith("https://") and token and sid), "product": PRODUCT, "demo": True, "affiliated_with_kapture": False, "recording": False, "mode": "turn-based speech and keypad", "language": "en-IN", "number_activation_verified": False}


@router.post("/incoming")
async def incoming(request: Request):
    await verified_form(request)
    root = Element("Response")
    gather(root, "Hello. I am Voxera, an independent AI website guide for Kapture C X. I am not affiliated with Kapture and this is not its official company phone line. Your speech is processed to answer your question. Do not share passwords, card details, or private account information. Calls are not recorded by this app. Ask about Kapture or its website. Press 1 for job applications, 2 to contact Kapture, 3 to request a demo, 4 for products, 9 for official support information, or 0 to end.")
    return xml_response(root)


@router.post("/turn")
async def turn(request: Request):
    form = await verified_form(request)
    root = Element("Response")
    try:
        number = max(0, int(request.query_params.get("turn", "0")))
        empty = max(0, int(request.query_params.get("empty", "0")))
    except ValueError:
        raise HTTPException(400, "Invalid turn")
    digit = form.get("Digits", "")
    speech = form.get("SpeechResult", "").strip()[:2000]
    if digit == "0" or speech.lower() in {"goodbye", "bye", "end call", "hang up"}:
        say(root, "Thank you for trying the Kapture website guide. Goodbye.")
        SubElement(root, "Hangup")
    elif number >= 12:
        say(root, "This demo has reached its call limit. Please use the browser support page for more help. Goodbye.")
        SubElement(root, "Hangup")
    elif digit == "9" or re.search(r"\b(human|agent|specialist|representative)\b", speech, re.I):
        gather(root, "This demo has no live human agent connected. Visit Kapture dot c x slash contact for official contact details, or slash support for customer help. No callback is promised. Ask another question, or press 0 to end.", number + 1)
    elif not digit and not speech:
        if empty >= 1:
            say(root, "I did not hear a response. Please call again when you are ready. Goodbye.")
            SubElement(root, "Hangup")
        else:
            gather(root, "I did not hear you. Please ask your question or press 1 for jobs, 2 for contact details, 3 for demos, 4 for products, or 0 to end.", number, empty + 1)
    else:
        questions = {"1": "apply jobs careers", "2": "contact Kapture email", "3": "request demo", "4": "products AgentOS"}
        if digit and digit not in questions:
            answer = "That keypad option is not available."
        else:
            from app import response_for
            answer, confidence, source, citation = response_for(questions.get(digit, speech), "en-IN")
            if source == "safe_fallback":
                answer = "I could not verify an answer in the reviewed official website guide. This demo cannot access your account or transfer you to a live agent. Please check the official Kapture website."
        gather(root, answer + " You can ask another question, press 9 for human support information, or press 0 to end.", number + 1)
    return xml_response(root)
