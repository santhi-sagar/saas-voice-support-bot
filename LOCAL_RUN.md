# Run Voxera permanently free on your computer

This mode does not need Render, a cloud account, an API key, a phone number, a domain, or recurring payment. It has no login and no re-verification step.

## One-time setup on Windows

1. Install Python 3.10 or newer from https://www.python.org/downloads/ and enable **Add Python to PATH**.
2. Double-click `START_VOXERA.bat`.
3. The first run creates `.venv` and installs the small local runtime. This is the only setup step that needs internet access.
4. Your browser opens at `http://127.0.0.1:8765`.

## Every later run

Double-click `START_VOXERA.bat` again. It starts the local bot without asking you to sign in or verify an account.

## Access code

The public-facing app has an access-code gate. On the first local run, Voxera generates a private code in `data/access_code.txt` and prints a message in the server window. Share that code only with approved customers. For a hosted deployment, set the private environment variable `VOXERA_ACCESS_CODE` in the host dashboard; never commit the code to GitHub.

## Voice use

Use Chrome or Edge, allow microphone permission once, select English, Telugu, or Hindi, and press **Tap to speak**. The text box remains available as a fallback. The browser's speech service is free to use, but browser support can vary; the support engine itself runs locally.

## What “always available” means here

The bot is available whenever this computer is powered on, connected to the local network, and the launcher is running. It is not publicly reachable from the internet by default. This is the only honest deployment model that avoids expiring free-hosting plans and provider re-verification.

To make it start automatically after Windows login, create a shortcut to `START_VOXERA.bat` in the Windows Startup folder (`Win+R`, then `shell:startup`).

## Data and privacy

The local SQLite database is stored in `data/voxera.db`. It is excluded from GitHub by `.gitignore`. Keep this folder private if it contains real customer conversations. The admin panel is intentionally local and has no cloud identity system; do not expose it to the public internet without adding authentication.
