@echo off
title VidVelocity PRO - Universal Video Downloader
color 0B
echo ===============================================================================
echo            VidVelocity PRO - Universal Video & Audio Downloader              
echo ===============================================================================
echo.
echo [1] Starting local download server...
echo [2] Download location: C:\Users\Hello\Downloads\wordpress\vid-downloader\Downloaded_Videos
echo [3] Opening web browser at http://localhost:5000 ...
echo.
echo Please leave this window open while downloading videos!
echo ===============================================================================

start "" "http://localhost:5000"
python app.py

pause
