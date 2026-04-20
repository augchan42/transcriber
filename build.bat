@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo   Building Video Transcriber .exe
echo ============================================
echo.

REM Find a Python launcher -- prefer "py" (Windows Python Launcher, always on PATH
REM after a normal Python install) and fall back to "python" if "py" isn't there.
REM This avoids depending on pip/pyinstaller being on PATH.
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py"
    goto :haspy
)
where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto :haspy
)

echo ERROR: Python not found!
echo.
echo Please install Python first:
echo   winget install Python.Python.3.12
echo.
pause
exit /b 1

:haspy
echo Using Python: %PY%
%PY% --version
echo.

echo Checking dependencies...

REM Install build dependencies via "python -m pip" so we don't rely on pip being on PATH.
%PY% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing pyinstaller...
    %PY% -m pip install pyinstaller
)

%PY% -m pip show faster-whisper >nul 2>&1
if errorlevel 1 (
    echo Installing faster-whisper...
    %PY% -m pip install faster-whisper
)

%PY% -m pip show yt-dlp >nul 2>&1
if errorlevel 1 (
    echo Installing yt-dlp...
    %PY% -m pip install yt-dlp
)

%PY% -m pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing requests...
    %PY% -m pip install requests
)

echo.
echo Building transcriber.exe...
echo.

REM Invoke PyInstaller via "python -m PyInstaller" so we don't rely on the
REM pyinstaller shim script being on PATH (pip sometimes installs it to a
REM Scripts folder that isn't on PATH).
%PY% -m PyInstaller --onefile --name transcriber --windowed ^
    --hidden-import faster_whisper ^
    --hidden-import ctranslate2 ^
    --hidden-import yt_dlp ^
    --hidden-import requests ^
    --hidden-import yt_auth ^
    --hidden-import yt_upload ^
    --hidden-import compress ^
    --collect-data faster_whisper ^
    --collect-data ctranslate2 ^
    gui.py

echo.
if errorlevel 1 (
    echo Build FAILED!
    pause
    exit /b 1
)

echo.
echo Copying OAuth client secret next to transcriber.exe...
if exist "secrets\client_secret_*.json" (
    if not exist "dist\secrets" mkdir "dist\secrets"
    copy /y "secrets\client_secret_*.json" "dist\secrets\" >nul
    echo   Copied client_secret to dist\secrets\
) else (
    echo   WARNING: no secrets\client_secret_*.json found -- YouTube upload will not work
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
echo Distribution folder contents:
echo   dist\transcriber.exe
echo   dist\secrets\client_secret_*.json    (YouTube OAuth)
echo.
echo Share the dist\ folder contents with your friend.
echo On first launch they click "Sign in to YouTube".
echo.
pause
