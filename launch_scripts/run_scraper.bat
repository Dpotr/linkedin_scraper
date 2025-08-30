@echo off
echo Starting LinkedIn Job Scraper...
echo.

REM Navigate to parent directory (one level up from launch_scripts)
cd /d "%~dp0.."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python and try again.
    echo.
    pause
    exit /b 1
)

REM Check if scraper script exists
if not exist "universal parser_wo_semantic_chatgpt.py" (
    echo ERROR: Scraper script not found in current directory.
    echo Expected: universal parser_wo_semantic_chatgpt.py
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

echo Running scraper from: %CD%
echo.
python "universal parser_wo_semantic_chatgpt.py"
echo.
echo Scraper finished. Press any key to close...
pause