@echo off
setlocal
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "TEMP=%~dp0.tmp_tests"
set "TMP=%~dp0.tmp_tests"
if not exist "%TEMP%" mkdir "%TEMP%"
python -B -m unittest discover -s tests -v
exit /b %ERRORLEVEL%
