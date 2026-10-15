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
LANGS={"en-IN":"English","hi-IN":"Hindi"}
HUMAN_RE=re.compile(r"\b(human|agent|specialist|representative)\b|मानव|एजेंट|कर्मचारी|प्रतिनिधि",re.I)


def configured():
    base=os.getenv("VOXERA_PUBLIC_URL","").rstrip("/")
    token=os.getenv("TWILIO_AUTH_TOKEN","")
    sid=os.getenv("TWILIO_ACCOUNT_SID","")
    return base,token,sid


async def verified_form(request):
    base,token,sid=configured()
    if not base.startswith("https://") or not token or not sid: raise HTTPException(503,"Phone service is not configured")
    raw=await request.body()
    if len(raw)>16000: raise HTTPException(413,"Payload too large")
    parsed=parse_qs(raw.decode("utf-8"),keep_blank_values=True)
    if any(len(v)!=1 for v in parsed.values()): raise HTTPException(400,"Duplicate parameters are not accepted")
    form={k:v[0] for k,v in parsed.items()}
    url=base+request.url.path
    if request.url.query: url+="?"+request.url.query
    message=url+"".join(k+form[k] for k in sorted(form))
    expected=base64.b64encode(hmac.new(token.encode(),message.encode(),hashlib.sha1).digest()).decode()
    if not hmac.compare_digest(request.headers.get("X-Twilio-Signature",""),expected): raise HTTPException(403,"Invalid provider signature")
    if form.get("AccountSid")!=sid or not re.fullmatch(r"CA[0-9a-fA-F]{32}",form.get("CallSid","")): raise HTTPException(403,"Unexpected account or call")
    return form


def xml_response(root): return Response(tostring(root,encoding="unicode"),media_type="application/xml")
def say(root,text,language="en-IN"): SubElement(root,"Say",{"language":language}).text=text


def gather(root,prompt,turn=0,empty=0,language="en-IN"):
    base,_,_=configured()
    action=base+"/api/voice/turn?"+urlencode({"turn":turn,"empty":empty,"lang":language})
    node=SubElement(root,"Gather",{"input":"speech dtmf","numDigits":"1","language":language,"speechTimeout":"auto","timeout":"6","actionOnEmptyResult":"true","action":action,"method":"POST"})
    say(node,prompt,language)
    return root


def intro_prompt():
    return ("Hello. I am Voxera, an independent AI website guide for Kapture C X. I am not affiliated with Kapture and this is not its official company phone line. Calls are not recorded by this app. Do not share passwords, card details, or private account information. Press 1 for English or 2 for Hindi.","नमस्ते। मैं Kapture CX के लिए स्वतंत्र AI वेबसाइट गाइड Voxera हूँ। मेरा Kapture से कोई संबंध नहीं है और यह उसकी आधिकारिक फ़ोन सेवा नहीं है। यह ऐप कॉल रिकॉर्ड नहीं करता। पासवर्ड, कार्ड विवरण या निजी खाते की जानकारी साझा न करें। हिंदी के लिए 2 दबाएँ, अंग्रेज़ी के लिए 1 दबाएँ।")


@router.get("/readiness")
def readiness():
    base,token,sid=configured()
    return {"configured":bool(base.startswith("https://") and token and sid),"product":PRODUCT,"demo":True,"affiliated_with_kapture":False,"recording":False,"mode":"turn-based speech and keypad","languages":["en-IN","hi-IN"],"number_activation_verified":False,"outbound_hr_calls_enabled":False}


@router.post("/incoming")
async def incoming(request:Request):
    await verified_form(request);root=Element("Response");en,hi=intro_prompt();base,_,_=configured()
    node=SubElement(root,"Gather",{"input":"dtmf","numDigits":"1","timeout":"7","action":base+"/api/voice/select-language","method":"POST"})
    say(node,en,"en-IN");say(node,hi,"hi-IN")
    return xml_response(root)


@router.post("/select-language")
async def select_language(request:Request):
    form=await verified_form(request);lang="hi-IN" if form.get("Digits")=="2" else "en-IN";root=Element("Response")
    prompt=("नमस्ते। मैं स्वतंत्र Kapture CX वेबसाइट गाइड हूँ। नौकरी के आवेदन के लिए 1, संपर्क के लिए 2, डेमो के लिए 3, उत्पादों के लिए 4, सहायता जानकारी के लिए 9, या समाप्त करने के लिए 0 दबाएँ अथवा अपना प्रश्न बोलें।" if lang=="hi-IN" else "Hello. I am an independent Kapture CX website guide. Ask a question or press 1 for job applications, 2 for contact, 3 for a demo, 4 for products, 9 for support information, or 0 to end.")
    gather(root,prompt,language=lang);return xml_response(root)


@router.post("/turn")
async def turn(request:Request):
    form=await verified_form(request);root=Element("Response")
    try: number=max(0,int(request.query_params.get("turn","0")));empty=max(0,int(request.query_params.get("empty","0")))
    except ValueError: raise HTTPException(400,"Invalid turn")
    lang=request.query_params.get("lang","en-IN");lang=lang if lang in LANGS else "en-IN";hi=lang=="hi-IN"
    digit=form.get("Digits","");speech=form.get("SpeechResult","").strip()[:2000]
    if digit=="0" or speech.lower() in {"goodbye","bye","end call","hang up"} or (hi and re.search(r"अलविदा|बंद करो|कॉल काटो",speech)):
        say(root,"Kapture वेबसाइट गाइड आज़माने के लिए धन्यवाद। नमस्ते।" if hi else "Thank you for trying the Kapture website guide. Goodbye.",lang);SubElement(root,"Hangup")
    elif number>=12:
        say(root,"इस डेमो की कॉल सीमा पूरी हो गई है। धन्यवाद।" if hi else "This demo has reached its call limit. Thank you.",lang);SubElement(root,"Hangup")
    elif digit=="9" or HUMAN_RE.search(speech):
        prompt="इस डेमो में कोई लाइव कर्मचारी नहीं है। Kapture की आधिकारिक संपर्क जानकारी के लिए kapture डॉट c x slash contact देखें। कॉलबैक का वादा नहीं है। अगला प्रश्न पूछें या समाप्त करने के लिए 0 दबाएँ।" if hi else "This demo has no live human agent. Visit Kapture dot c x slash contact for official contact details. No callback is promised. Ask another question or press 0 to end."
        gather(root,prompt,number+1,language=lang)
    elif not digit and not speech:
        if empty>=1:
            say(root,"आपकी आवाज़ सुनाई नहीं दी। कृपया बाद में फिर प्रयास करें।" if hi else "I did not hear a response. Please try again later.",lang);SubElement(root,"Hangup")
        else:
            prompt="आपका प्रश्न बोलें या नौकरी के लिए 1, संपर्क के लिए 2, डेमो के लिए 3, उत्पादों के लिए 4, समाप्त करने के लिए 0 दबाएँ।" if hi else "Please ask your question or press 1 for jobs, 2 for contact, 3 for a demo, 4 for products, or 0 to end."
            gather(root,prompt,number,empty+1,lang)
    else:
        questions={"1":"apply jobs careers","2":"contact Kapture email","3":"request demo","4":"products AgentOS"}
        if digit and digit not in questions:
            answer="यह विकल्प उपलब्ध नहीं है।" if hi else "That keypad option is not available."
        else:
            from app import response_for
            answer,confidence,source,citation=response_for(questions.get(digit,speech),lang)
            if source=="safe_fallback": answer="आधिकारिक वेबसाइट गाइड में इसका सत्यापित उत्तर नहीं मिला। कृपया Kapture की आधिकारिक वेबसाइट देखें।" if hi else "I could not verify an answer in the reviewed official website guide. Please check the official Kapture website."
        continuation="अगला प्रश्न पूछें, सहायता जानकारी के लिए 9 दबाएँ, या समाप्त करने के लिए 0 दबाएँ।" if hi else "Ask another question, press 9 for support information, or 0 to end."
        gather(root,answer+" "+continuation,number+1,language=lang)
    return xml_response(root)
