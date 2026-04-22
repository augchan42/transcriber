@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
echo ============================================
echo   Package TranscriberPortable for Release
echo ============================================
echo.

REM --- Step 1: Build the exe ---
echo Step 1/4: Building transcriber.exe ...
call build.bat
if errorlevel 1 (
    echo Build failed — aborting release.
    pause
    exit /b 1
)

REM --- Step 2: Assemble TranscriberPortable folder ---
echo.
echo Step 2/4: Assembling TranscriberPortable folder ...

set "OUT=TranscriberPortable"
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%"

copy /y dist\transcriber.exe "%OUT%\" >nul
echo   Copied transcriber.exe

REM Copy ffmpeg + ffprobe from PATH (skip ffplay — not used)
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo   WARNING: ffmpeg not on PATH — copy ffmpeg.exe and ffprobe.exe manually
) else (
    for /f "delims=" %%F in ('where ffmpeg') do (
        copy /y "%%F" "%OUT%\" >nul
        echo   Copied ffmpeg.exe
        REM ffprobe should be in the same directory
        for %%D in ("%%~dpF") do (
            if exist "%%~Dffprobe.exe" (
                copy /y "%%~Dffprobe.exe" "%OUT%\" >nul
                echo   Copied ffprobe.exe
            ) else (
                echo   WARNING: ffprobe.exe not found next to ffmpeg — copy it manually
            )
        )
    )
)

REM NOTE: we deliberately do NOT bundle secrets\client_secret_*.json.
REM This is an open-source release — users bring their own Google OAuth
REM client (see docs\youtube-setup.md). The secrets\ folder is created
REM empty so the app can drop yt-tokens.json there after sign-in.
if not exist "%OUT%\secrets" mkdir "%OUT%\secrets"
echo   Created empty secrets\ folder (users add client_secret_*.json themselves)

REM Copy the BYO-credentials setup guide
if exist "docs\youtube-setup.md" (
    copy /y "docs\youtube-setup.md" "%OUT%\youtube-setup.md" >nul
    echo   Copied youtube-setup.md
)

REM Create README
(
echo Video Transcriber - Quick Start
echo ==============================
echo.
echo 1. Double-click transcriber.exe
echo 2. Pick your video file
echo 3. Choose language ^(use "Chinese ^(zh^)" for Cantonese^)
echo 4. Click Transcribe
echo.
echo Done! Subtitle files ^(.srt and .txt^) will appear next to your video.
echo.
echo Note: On first run, it will download the speech model ^(~150MB^).
echo After that it works offline.
echo.
echo.
echo YouTube Upload ^(optional^)
echo -------------------------
echo The app can compress videos for YouTube and upload them with
echo auto-resume if the network drops.
echo.
echo First-time setup: you need your own Google OAuth credentials.
echo See youtube-setup.md ^(next to this file^) for a 5-minute walkthrough.
echo.
echo Once you have the credentials file in secrets\:
echo 1. Click "Sign in to YouTube" -- browser opens, approve the app
echo 2. Pick a video, enter a title, pick privacy, click Upload
echo 3. If upload fails partway, click Upload again -- it resumes
) > "%OUT%\README.txt"
echo   Created README.txt

REM --- Step 3: Zip ---
echo.
echo Step 3/4: Creating TranscriberPortable.zip ...

if exist TranscriberPortable.zip del TranscriberPortable.zip

REM Try PowerShell (available on all modern Windows)
powershell -NoProfile -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath 'TranscriberPortable.zip' -Force"
if errorlevel 1 (
    echo   PowerShell zip failed — please zip TranscriberPortable\ manually
) else (
    echo   Created TranscriberPortable.zip
)

REM --- Step 4: Show summary and next steps ---
echo.
echo ============================================
echo   Release package ready!
echo ============================================
echo.
echo   Folder: %OUT%\
dir /b "%OUT%"
echo.

if exist TranscriberPortable.zip (
    for %%Z in (TranscriberPortable.zip) do echo   Zip size: %%~zZ bytes

    REM Compute SHA256 for winget manifest
    for /f "tokens=*" %%H in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 'TranscriberPortable.zip').Hash"') do (
        if not defined ZIP_SHA256 set "ZIP_SHA256=%%H"
    )
    echo   SHA256:   !ZIP_SHA256!
    echo.
    echo   To publish on GitHub:
    echo     gh release create vX.Y.Z TranscriberPortable.zip --title "Video Transcriber vX.Y.Z" --notes "..."
    echo.
    echo   For the winget manifest, use:
    echo     InstallerUrl:    https://github.com/augchan42/transcriber/releases/download/vX.Y.Z/TranscriberPortable.zip
    echo     InstallerSha256: !ZIP_SHA256!
)
echo.
pause
