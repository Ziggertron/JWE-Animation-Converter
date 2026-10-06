@echo off
cd /d "%~dp0"
python -m pip install pyinstaller
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name JWE-Animation-Converter app.py
if errorlevel 1 exit /b 1
copy /y dist\JWE-Animation-Converter.exe .
pause
