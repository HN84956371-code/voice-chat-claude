@echo off
chcp 65001 >nul
title Voice Chat with Claude
python -u "%~dp0voice_chat.py"
pause
