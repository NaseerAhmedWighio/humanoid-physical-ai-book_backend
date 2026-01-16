@echo off
REM Batch script to run the agent test

echo Running AI Agent Terminal Test...
echo.

REM Activate the virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
)

REM Run the test script
python scripts\test_agent.py

REM Pause to see the output
pause