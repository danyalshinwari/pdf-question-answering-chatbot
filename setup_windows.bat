@echo off
rem Work inside this script's directory, including paths that contain spaces.
cd /d "%~dp0"
rem Prefer the Windows Python launcher, falling back to python on PATH.
where py >nul 2>nul
if errorlevel 1 (set "PY_CMD=python") else (set "PY_CMD=py -3")
rem Create the environment once; keep an existing environment intact.
if not exist ".venv\Scripts\python.exe" %PY_CMD% -m venv .venv
if errorlevel 1 goto failed
rem Install the light core dependencies for an immediate first run.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
rem Create a local configuration template without overwriting an existing key.
if not exist ".env" copy ".env.example" ".env" >nul
rem Tell the user exactly what to open next.
echo Setup complete. Double-click run_windows.bat.
pause
exit /b 0
:failed
rem Keep the window open so the installation error can be read.
echo Setup failed. Install 64-bit Python 3.11 or 3.12 and see README.md.
pause
exit /b 1
