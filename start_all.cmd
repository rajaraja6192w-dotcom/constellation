@echo off
echo ========================================
echo   CONSTELLATION V2 - STARTUP SCRIPT
echo ========================================
echo.

echo [1/2] Starting Main Bot...
start "Constellation Bot" cmd /k "python main.py"

echo [2/2] Starting Ko-fi Webhook Server...
timeout /t 2 /nobreak > nul
start "Ko-fi Webhook" cmd /k "python kofi_webhook.py"

echo.
echo ========================================
echo   ✅ BOTH SERVICES STARTED!
echo ========================================
echo.
echo 🤖 Main Bot: Running in window "Constellation Bot"
echo    → Test: Send /start to your Telegram bot
echo.
echo 🌐 Webhook: Running in window "Ko-fi Webhook"
echo    → Test: http://localhost:5000/health
echo.
echo 💡 TIP: Keep both windows open while bot is running
echo    Close windows to stop services
echo.
echo ========================================
pause
