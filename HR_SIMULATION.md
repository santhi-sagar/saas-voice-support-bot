# Voxera HR interview-practice simulation

## Current implementation
A user-initiated, browser-only HR screening practice flow alongside the independent Kapture CX website guide. It is explicitly not a Kapture HR interview, not an employment offer, and not a hiring decision. It supports English (India) and Hindi prompts and speech input/output where the browser provides those capabilities.

Prompts: role of interest; highest education/field/year; relevant experience; previous relevant work (optional); skills/projects; preferred interview days/times. Users may skip or stop. Preferred times are collected only—there is no calendar check, slot selection, or booking.

The practice script asks users to use synthetic information. Answers stay in page memory only and are rendered locally in a completion summary; they are not sent to Voxera's APIs or stored by this app, and are cleared when the dialog closes. Browser speech recognition may process audio using browser/provider speech services; do not enter real candidate PII. Browser/browser-provider behaviour should be reviewed before any real candidate use.

## Live recruiting calls are not implemented or enabled
The deployed Twilio module currently supports only inbound English Kapture website FAQ calls. It has no outbound candidate-dial route. The readiness endpoint explicitly reports outbound HR calls disabled. No number is verified. No candidate has been called.

Do not turn this mock flow into real recruitment until the employer/client is identified, authority to represent that employer is documented, candidate contact source and consent/notice/opt-out process are established, privacy/retention and access controls are defined, and approved interview script and role-specific questions are reviewed. If real calls are later built, use a separate consent-first inbound/outbound workflow, no sensitive data collection, no hiring scores/decisions, no unverified live slots, explicit AI disclosure, and per-call user approval covering exact recipient, script, timing, and cost. Never purchase numbers or place calls without separate explicit approval.

## Tests
`test_phone.py` includes source/structure checks for the HR simulation being separate from the API, bilingual prompts, data-minimising disclaimer, and disabled outbound calling. Existing Kapture topic and Twilio webhook tests remain.
