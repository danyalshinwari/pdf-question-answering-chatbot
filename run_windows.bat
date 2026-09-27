@echo off
rem Use this project folder even when launched by double-clicking.
cd /d "%~dp0"
rem Explain the missing environment instead of launching an unrelated Python.
if not exist ".venv\Scripts\python.exe" (
 echo Run setup_windows.bat first.
 pause
 exit /b 1
)
rem Bind to the local computer; keep this learning app off the public network.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1
rem Keep any startup error visible when the server exits.
pause
