@echo off
rem Double-click or run from Command Prompt. Wraps setup.ps1 and bypasses the
rem PowerShell execution policy for this single run only (no system change).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1" %*
set EXITCODE=%ERRORLEVEL%
echo %cmdcmdline% | find /i "%~nx0" >nul && pause
exit /b %EXITCODE%
