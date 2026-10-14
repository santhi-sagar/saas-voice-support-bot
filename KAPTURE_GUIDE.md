# Voxera — Independent Kapture CX Website Guide

## Purpose
An independent voice/text demo that explains Kapture CX's public website. Not affiliated with, endorsed by, or connected to Kapture CX staff. It does not submit applications or enquiries, access customer accounts, or promise a callback. English-only in this reviewed version. Browser voice and inbound phone support are turn-based; grounded guide retrieval is used, not a generative LLM.

## Reviewed topics
Company overview; products/AgentOS/VITOS/COMMAND/CALIBRATE/PULSE; website navigation; applying for jobs; published hiring stages; contacting the company; booking a demo; pricing/quotes; customer support/login guidance; office location; integrations/API documentation; partnerships; trust/security/privacy routes.

## Official sources checked on 13 October 2026
- Homepage/navigation/products: https://www.kapture.cx/
- Company: https://www.kapture.cx/about-us/
- Careers/application routes/process: https://www.kapture.cx/careers/
- Example Keka role reached through careers: https://kapturecrm.keka.com/careers/jobdetails/157852
- Contact/office/general email: https://www.kapture.cx/contact/
- Demo form: https://www.kapture.cx/demo/
- Customer support form: https://www.kapture.cx/support/
- Pricing/quote approach: https://www.kapture.cx/pricing/
- Partners: https://www.kapture.cx/partner/
- Trust Center: https://www.kapture.cx/trust-center/
- Integrations: https://www.kapture.cx/integrations/

This is a bounded review of main website routes, not every website page. Claims are company-published information, not independently audited assurances. Sources can change. Specific vacancy availability and complete Keka application fields were not verified. Do not claim current openings, timelines, salary, virtual-only hiring, a universal login URL, or commercial guarantees. Phone formatting differs across official pages; direct users to Contact Us to verify numbers before dialing.

## Answer serving
The versioned reviewed JSON pack in data/kapture_guide.json is the sole website-answer source. Legacy SaaS SQLite articles remain preserved but are excluded from customer answers. Existing legacy admin editing does not update this guide. To update the guide, verify official pages, revise the JSON and tests, and publish the reviewed version. Each answer includes its official source URL and review date. Topic match scores are routing scores, not calibrated accuracy probabilities. Unverified questions use safe fallback.

## Phone controls
1: careers/applications; 2: contact; 3: demo; 4: products; 9: official support information; 0: hangup. No live transfer, outbound calls, audio recording, or persisted phone transcripts. Twilio may retain its own call metadata.

## Deployment and testing
See PHONE_SETUP.md for secure environment settings, signature validation, number configuration, and live acceptance checklist. Tests: uv run --no-project --with fastapi==0.115.6 --with httpx python test_phone.py. 13 tests passed, including a 12-question topic matrix, unsupported requests, exclusion of old SaaS answers, and inbound webhook flows. JavaScript syntax checked with node --check static/app.js.

Real phone activation is pending until settings are saved/deployed, a voice-enabled number is configured, and a successful live call is verified. Render free-tier cold starts and trial limits mean this is not a guaranteed always-on production line.
