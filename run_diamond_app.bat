@echo off
echo Starting Shree Dangigev Diamonds (SDD) Accounting App...
cd "D:\NV SOFTWARE BY CURSOR"

:: Check if virtual environment exists and activate it
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Using system Python.
)

:: Start the Flask app in the background
start /B python -m diamond_accounting_app.app

:: Wait a moment for the server to start
timeout /t 3 /nobreak > nul

:: Open the default browser
start http://127.0.0.1:5000

echo Application started! The browser should open automatically.
echo To stop the application, close this window or press Ctrl+C. 