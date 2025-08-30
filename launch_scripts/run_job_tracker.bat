@echo off
echo Starting Job Tracker Dashboard...
echo Opening in your browser at http://localhost:8501
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

REM Check if Streamlit is available
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit not found. Please install with: pip install streamlit
    echo.
    pause
    exit /b 1
)

REM Check if job tracker script exists
if not exist "job_tracker.py" (
    echo ERROR: Job Tracker script not found in current directory.
    echo Expected: job_tracker.py
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)

echo Running Job Tracker from: %CD%
echo.
streamlit run job_tracker.py
echo.
echo Dashboard closed. Press any key to close...
pause