# Setup Guide (Windows 10/11)

Follow the steps in order. Steps marked **(you)** are done by you; the scripts do the rest.

## 1. Windows prerequisites (you)
- Windows 10 or 11, 64-bit, with at least 2 GB free disk space.
- Internet access during setup (to download Python packages and the Playwright browser).
- PowerShell 5.1 (built in). No administrator rights are required for Phase 2.

## 2. Install Python (you)
1. Download **Python 3.12.x (64-bit)** from <https://www.python.org/downloads/windows/>.
2. In the installer tick **"Add python.exe to PATH"** and keep the **py launcher** option.
3. Open a new PowerShell window and check:
   ```powershell
   py -3.12 --version
   ```
   Expected: `Python 3.12.x`. (3.13 also works; older or newer versions are rejected by setup.)

## 3. Install Git (you)
Install from <https://git-scm.com/download/win> (defaults are fine), then check `git --version`.

## 4. Create the project folder (you)
Copy the delivered project folder to a path without spaces, for example
`C:\Projects\local-ai-task-automation`, then:
```powershell
cd C:\Projects\local-ai-task-automation
git init
```

## 5-8. Virtual environment, dependencies, Playwright, database (one script)
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install\setup.ps1
```
The script is safe to re-run. It: finds Python, creates `.venv`, installs the pinned dependencies,
installs the Playwright Chromium test browser, creates `.env` from `.env.example`, creates the
runtime folders, initialises `database\automation.db`, verifies the environment, and runs the tests.
Options: `-SkipBrowserInstall`, `-SkipTests`, `-PythonCommand "C:\path\to\python.exe"`.

You can also double-click `scripts\install\setup.bat`.

### Doing it manually (equivalent)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1          # PowerShell   (Command Prompt: .\.venv\Scripts\activate.bat)
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
copy .env.example .env
python scripts\install\init_environment.py
python scripts\diagnostics\verify_environment.py
```
If activation is blocked, see `docs/TROUBLESHOOTING.md` (or use `.\.venv\Scripts\python.exe` directly).

### About Playwright
- The Python package is installed with the other dependencies.
- `python -m playwright install chromium` downloads one test browser (about 150 MB) to
  `%LOCALAPPDATA%\ms-playwright`. It is used for deterministic tests only.
- Real automation (Phase 5+) uses your installed Chrome, Brave and Edge through *dedicated automation
  profiles* stored under `profiles\`. Your normal personal browser profiles are never used or copied.
- Verify: `python scripts\diagnostics\verify_environment.py` should show "Playwright ... driver initialises".

## 9. Start the application
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```
Open <http://127.0.0.1:8000>. You should see **Backend ONLINE**, **Database CONNECTED**,
**Python environment READY**. Stop with `Ctrl+C`.

Useful URLs: `/api/v1/health`, `/api/v1/health/database`, `/api/v1/health/environment`,
`/api/v1/system/info`, `/docs` (API explorer, development only).

## 10. Run the tests
```powershell
.\.venv\Scripts\python.exe -m pytest
```
Expected: all tests pass (one test, `test_pywinauto_installed_on_windows`, runs only on Windows).
