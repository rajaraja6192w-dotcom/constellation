@echo off
echo ========================================
echo   GITHUB SETUP FOR RAILWAY DEPLOYMENT
echo ========================================
echo.

echo This script will help you push your code to GitHub
echo Then you can deploy it on Railway
echo.

echo Step 1: Initialize Git Repository
git init
echo.

echo Step 2: Add all files
git add .
echo.

echo Step 3: Create initial commit
git commit -m "Initial commit - Constellation V2 ready for Railway"
echo.

echo ========================================
echo   GIT REPOSITORY INITIALIZED!
echo ========================================
echo.

echo Next steps:
echo.
echo 1. Create a new repository on GitHub:
echo    → Go to: https://github.com/new
echo    → Name: constellation-bot
echo    → Make it Private (recommended)
echo    → DO NOT initialize with README
echo    → Click "Create repository"
echo.

echo 2. Push your code (replace YOUR_USERNAME):
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/constellation-bot.git
echo    git branch -M main
echo    git push -u origin main
echo.

echo 3. Then deploy on Railway:
echo    → Go to: https://railway.app
echo    → New Project → Deploy from GitHub
echo    → Select your repository
echo    → Add BOT_TOKEN environment variable
echo    → Deploy!
echo.

echo ========================================
pause
