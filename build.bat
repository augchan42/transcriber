@echo off
echo ============================================
echo   Building Video Transcriber .exe
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo.
    echo Please install Python first:
    echo   winget install Python.Python.3.12
    echo.
    pause
    exit /b 1
)

echo Checking dependencies...

REM Install build dependencies
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing pyinstaller...
    pip install pyinstaller
)

pip show faster-whisper >nul 2>&1
if errorlevel 1 (
    echo Installing faster-whisper...
    pip install faster-whisper
)

pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo Installing yt-dlp...
    pip install yt-dlp
)

pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing requests...
    pip install requests
)

echo.
echo Building transcriber.exe...
echo.

pyinstaller --onefile --name transcriber --windowed --hidden-import faster_whisper --hidden-import ctranslate2 --hidden-import yt_dlp --hidden-import requests --collect-data faster_whisper --collect-data ctranslate2 gui.py

echo.
if errorlevel 1 (
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build successful!
echo ============================================
echo.
echo Your exe is at: dist\transcriber.exe
echo.
echo To use it, you'll need ffmpeg:
echo   winget install ffmpeg
echo.
echo Share dist\transcriber.exe with your friend.
echo.
pause
