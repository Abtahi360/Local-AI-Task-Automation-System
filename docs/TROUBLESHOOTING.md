# Troubleshooting

## Python not found
`setup.ps1` reports "Python 3.12 or 3.13 was not found". Install Python 3.12.x from python.org with
**Add python.exe to PATH**, open a *new* PowerShell window, check `py -3.12 --version`. If `python`
opens the Microsoft Store, turn off *Settings > Apps > Advanced app settings > App execution aliases*
for python.exe, or pass `-PythonCommand "C:\Path\To\python.exe"`.

## Virtual environment activation is blocked
Error: "running scripts is disabled on this system". Use either:
- the provided wrappers (`setup.bat`, `start.bat`) or `powershell -ExecutionPolicy Bypass -File ...`
  (affects that one run only), or
- `.\.venv\Scripts\python.exe -m ...` without activating, or
- Command Prompt activation: `.\.venv\Scripts\activate.bat`, or
- `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (your account only).

## pip installation failure
- Check internet/proxy access; retry. Corporate proxy: set `HTTPS_PROXY`.
- Use Python 3.12 or 3.13 (64-bit). 32-bit Python lacks wheels for some packages.
- `python -m pip install --upgrade pip`, then re-run setup.
- Read the first error line, not the last; send it to the AI developer.

## Dependency version conflicts
Run `python -m pip check`. Install only from the pinned files; do not `pip install` extra packages
into `.venv`. If broken, delete the `.venv` folder and re-run setup (no project data lives there).

## Playwright browser installation failure
The browser download is optional in Phase 2. Retry `python -m playwright install chromium`; check
firewall/proxy and disk space. Verify with `python scripts\diagnostics\verify_environment.py`
(the Chromium line may show WARN; the overall result can still be PASS).

## SQLite initialisation failure
- Run `python scripts\install\init_environment.py` and read the message.
- "unable to open database file": the folder is not writable or `DATABASE_PATH` is wrong/a folder.
- "database is locked": close other programs using `database\automation.db`.
- Do not store the project in a synced or network folder (OneDrive, network share): WAL mode is unreliable there.

## Port already in use
`start.ps1` says "Port 8000 is already in use". Close the other program, or set `APP_PORT=8001`
in `.env`. Find the owner: `netstat -ano | findstr :8000`.

## FastAPI will not start
- Run `python -m backend` directly to see the error.
- "APP_HOST ... is not a loopback address": set `APP_HOST=127.0.0.1` in `.env`.
- Invalid `.env` values (for example `LOG_LEVEL=LOUD`) stop startup with a clear message.
- Run `python scripts\diagnostics\verify_environment.py`.
- Logs: `logs\application.log`.

## Missing Windows permissions
Phase 2 needs no administrator rights. Allow Python through Windows Firewall only if prompted (the
server listens on localhost). Antivirus may slow or block the first Playwright download; allow it and retry.

## The status page says OFFLINE
The server is not running. Start `scripts\start.ps1` and reload `http://127.0.0.1:8000`.
