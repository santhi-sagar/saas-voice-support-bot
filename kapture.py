"""Reviewed official-site guide. No old SaaS articles are used to answer."""
import json
import re
from pathlib import Path

CHECKED = '2026-10-13'
GUIDES = json.loads((Path(__file__).parent / 'data' / 'kapture_guide.json').read_text(encoding='utf-8'))
GREETING = 'Hello. I am Voxera, an independent AI website guide for Kapture CX, not an official Kapture representative. Ask what the company does, how to apply for jobs, request a demo, or contact them. I explain public website information; I cannot submit forms or access accounts.'
FALLBACK = 'I could not verify a specific answer in the reviewed Kapture website guide. Please check the relevant official page or contact Kapture directly. I cannot invent job openings, salaries, prices, account details, or promises.'


def answer(message, language='en-IN'):
    text = message.lower().strip()
    if len(text) > 2000:
        return FALLBACK, 0.0, 'safe_fallback', None
    if re.search(r'\b(ignore.*instructions|system prompt|salary|salaries|guarantee|guaranteed|otp|my application status|my ticket status|currently hiring|current vacancies|latest vacancies|open jobs today|refund approved)\b', text):
        return FALLBACK, 0.0, 'safe_fallback', {'title':'Check official Kapture information', 'url':'https://www.kapture.cx/contact/', 'checked_at':CHECKED}
    if text in {'hi','hello','hey','good morning'}:
        return GREETING, 1.0, 'knowledge_base', {'title':'Kapture official website','url':'https://www.kapture.cx/','checked_at':CHECKED}
    # Specific topics take precedence over generic company/website wording.
    order = [2,1,4,6,8,10,11,12,7,5,3,9,0]
    matches = [GUIDES[i] for i in order if re.search(GUIDES[i]['pattern'],text)]
    if not matches:
        return FALLBACK, 0.0, 'safe_fallback', {'title':'Kapture official website','url':'https://www.kapture.cx/','checked_at':CHECKED}
    guide = matches[0]
    # This is a routing score, not a calibrated probability of correctness.
    return guide['content'], 0.9, 'knowledge_base', {'title':guide['title'], 'url':guide['url'], 'checked_at':CHECKED,'version':1,'steps':[], 'scope':'official-site guide, not live account data'}
