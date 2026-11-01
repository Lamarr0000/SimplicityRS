@echo off
"C:\SimplicityAI-Lab\ThemHands\.venv\Scripts\python.exe" "%~dp0launch.py" --model qwen3:8b
if errorlevel 1 pause
