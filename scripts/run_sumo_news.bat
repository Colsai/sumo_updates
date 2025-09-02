@echo off
REM Sumo News Weekly Digest Runner
REM This script runs the sumo news application and logs output

REM Set the working directory to the project root (parent of scripts)
cd /d "%~dp0\.."

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set log file with timestamp
set TIMESTAMP=%date:~10,4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOGFILE=logs\sumo_news_%TIMESTAMP%.log

echo Starting Sumo News Digest at %date% %time% > %LOGFILE%
echo ============================================== >> %LOGFILE%

REM Change to src directory and run the application
cd src
python main.py >> ..\%LOGFILE% 2>&1

REM Log completion
echo. >> ..\%LOGFILE%
echo ============================================== >> ..\%LOGFILE%
echo Completed Sumo News Digest at %date% %time% >> ..\%LOGFILE%

REM Return to project root
cd ..

REM Optional: Keep only last 10 log files
forfiles /p logs /m sumo_news_*.log /c "cmd /c del @path" /d -30 >nul 2>&1

echo Sumo News Digest completed. Check %LOGFILE% for details.