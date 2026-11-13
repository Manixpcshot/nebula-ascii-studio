@echo off
title NEBULA ASCII STUDIO v3.0 — High-Fidelity Image-to-ASCII Engine
chcp 65001 >nul
cd /d "%~dp0"

py main.py %*

if %errorlevel% neq 0 (
    echo.
    pause
)
