@echo off
setlocal
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

REM Copy OAuth client secret
if exist "secrets\client_secret_*.json" (
    if not exist "%OUT%\secrets" mkdir "%OUT%\secrets"
    copy /y "secrets\client_secret_*.json" "%OUT%\secrets\" >nul
    echo   Copied client_secret to secrets\
) else (
    echo   WARNING: no secrets\client_secret_*.json — YouTube upload won't work
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
echo The app can compress videos for YouTube and upload them directly to
echo the shared podcast channel with auto-resume if the network drops.
echo.
echo First-time setup ^(once^):
echo 1. Pick any video, then click "Sign in to YouTube"
echo 2. A browser opens -- sign in with the shared podcast Google account
echo 3. Approve the permissions
echo.
echo Every upload after that:
echo 1. Click "Compress for YouTube" ^(optional but recommended^)
echo 2. Pick the _compressed.mp4 file
echo 3. Enter a title, pick Privacy ^(unlisted / private / public^)
echo 4. Click "Upload to YouTube"
echo.
echo If the upload fails partway, just click Upload again -- it resumes
echo from where it stopped.
echo.
echo Requires a "secrets/" folder next to transcriber.exe containing
echo client_secret_*.json. Your tech friend has already put it there.
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
    echo.
    echo   To publish on GitHub:
    echo     gh release create v2.0.0 TranscriberPortable.zip --title "Video Transcriber v2.0.0" --notes "..."
    echo.
    echo   Or just send TranscriberPortable.zip directly to your friend.
)
echo.
pause
