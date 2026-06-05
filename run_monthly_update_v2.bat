@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   [Cominets] Data Update Batch (Auto-Repair Pipeline v3.0)
echo ============================================================
echo.

echo ------------------------------------------------------------
echo [INFO] Checking required libraries...
echo ------------------------------------------------------------
python -c "import selenium, win32com, requests, google.oauth2" 2>nul
if errorlevel 1 (
    echo Required libraries [selenium, pywin32, requests, google-auth] are missing.
    echo Installing...
    python -m pip install selenium pywin32 requests google-auth
    if errorlevel 1 (
        echo [ERROR] Installation failed. Check internet connection or run manual command:
        echo   pip install selenium pywin32 requests google-auth
        pause
        exit /b 1
    )
    echo Installation complete.
)

echo.
echo [INFO] Starting Edge browser on debug port 9222...
echo.

start "" launch_edge.bat
timeout /t 5 >nul

set "RUN_MODE=auto"
set "TARGET_MONTH="

:: Check if non-interactive mode is requested via CLI argument
if "%~1"=="auto" (
    echo [INFO] Running in non-interactive automatic mode.
    set "RUN_MODE=auto"
    goto START_PROCESS
)

choice /c yn /t 10 /d n /m "Do you want to specify target month manually? (Default: N in 10s)"
if %errorlevel% equ 1 (
    set "RUN_MODE=manual"
    set /p TARGET_MONTH="Enter Target Month (Format: YYYY/MM) [Press Enter for Previous Month]: "
)

:START_PROCESS
echo.
echo ------------------------------------------------------------
echo [STEP 1/5] QuickSight Date Filter Setting...
echo ------------------------------------------------------------
if "!RUN_MODE!"=="auto" (
    python step_1_date_monthly.py auto
) else (
    if "!TARGET_MONTH!"=="" (
        python step_1_date_monthly.py
    ) else (
        python step_1_date_monthly.py !TARGET_MONTH!
    )
)
if %ERRORLEVEL% neq 0 goto ERR_DATE

:: --- Auto-Repair Pipeline Loop ---
set LOOP_COUNT=0
set MAX_LOOPS=3

:REPAIR_LOOP
set /a LOOP_COUNT+=1
echo.
echo ============================================================
echo   [REPAIR LOOP] Attempt !LOOP_COUNT! of !MAX_LOOPS!
echo ============================================================

echo ------------------------------------------------------------
echo [STEP 2/5] Verifying X-Drive and Firestore Status (Scan)...
echo ------------------------------------------------------------
python process_data.py --scan-only
set SCAN_RES=%ERRORLEVEL%

if %SCAN_RES% equ 0 (
    echo.
    echo ------------------------------------------------------------
    echo   [SUCCESS] All data matched and synced.
    echo   Skipping RPA extraction and proceeding to final sync...
    echo ------------------------------------------------------------
    goto SYNC_PROCESS
)

if !LOOP_COUNT! gtr !MAX_LOOPS! (
    echo [ERROR] Reached max loops [!MAX_LOOPS!] but some data are still missing.
    goto ERR_EXTRACT
)

echo ------------------------------------------------------------
echo [STEP 3/5] RPA Data Extraction (Targeted and micro-targeted)...
echo ------------------------------------------------------------
python rpa_extractor_monthly.py
:: Continue loop even if RPA warns, to retry on next cycle.

echo ------------------------------------------------------------
echo [STEP 4/5] Merging Extracted Data into Master ZIPs...
echo ------------------------------------------------------------
python merge_monthly_data.py

:SYNC_PROCESS
echo ------------------------------------------------------------
echo [STEP 5/5] Processing Data and Syncing to Firestore...
echo ------------------------------------------------------------
python process_data.py
if %ERRORLEVEL% neq 0 goto ERR_SYNC

:: Final check after sync
echo.
echo ------------------------------------------------------------
echo [FINAL CHECK] Verifying Sync Status...
echo ------------------------------------------------------------
python process_data.py --scan-only
set FINAL_SCAN=%ERRORLEVEL%

if %FINAL_SCAN% neq 0 (
    if !LOOP_COUNT! lss !MAX_LOOPS! (
        echo [INFO] Some data are still missing. Continuing repair loop...
        goto REPAIR_LOOP
    ) else (
        echo [ERROR] All repair attempts completed but sync is still incomplete.
        goto ERR_SYNC
    )
)

:: Cleanup missing patterns tracking file if success
if exist missing_patterns.json del missing_patterns.json

echo.
echo ------------------------------------------------------------
echo [REPORT] Sending completion mail report...
echo ------------------------------------------------------------
python send_report_mail.py

echo.
echo ============================================================
echo   [FINISHED] All data update and sync tasks completed.
echo ============================================================
goto END

:ERR_DATE
echo [ERROR] Failed to set date. Processing aborted.
goto ERR_PAUSE

:ERR_EXTRACT
echo [ERROR] Failed to extract data after multiple attempts.
python send_report_mail.py
goto ERR_PAUSE

:ERR_MERGE
echo [ERROR] Failed to merge data. Check temp folder.
python send_report_mail.py
goto ERR_PAUSE

:ERR_SYNC
echo [ERROR] Failed to sync data to Firestore.
python send_report_mail.py
goto ERR_PAUSE

:ERR_PAUSE
if "!RUN_MODE!"=="manual" (
    pause
)
exit /b 1

:END
echo.
if "!RUN_MODE!"=="manual" (
    pause
)
exit /b 0
