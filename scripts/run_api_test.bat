@echo off
REM Batch script to run the API test

echo Running AI Textbook Backend API Test...
echo.

REM Activate the virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
)

REM Run the API test script
python scripts\test_api.py

REM Pause to see the output
pause