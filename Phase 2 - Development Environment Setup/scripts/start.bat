@echo off
rem Wraps start.ps1 and bypasses the PowerShell execution policy for this run only.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
exit /b %ERRORLEVEL%
