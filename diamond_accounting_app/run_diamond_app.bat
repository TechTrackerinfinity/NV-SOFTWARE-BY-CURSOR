@echo off
echo Starting Shree Dangigev Diamonds (SDD) Accounting App...
cd "D:\NV SOFTWARE BY CURSOR\diamond_accounting_app"
call venv\Scripts\activate.bat

:: Start the Flask app in the background
start /B python app.py

:: Wait a moment for the server to start
timeout /t 3 /nobreak > nul

:: Open the default browser
start http://localhost:5000

echo Application started! The browser should open automatically.
echo To stop the application, close this window or press Ctrl+C.