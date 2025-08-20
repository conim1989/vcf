@echo off
REM Windows batch script for GitHub commits
echo === VCF Processor GitHub Commit Tool ===

REM Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the Python script
python commit_to_github.py %*
pause
