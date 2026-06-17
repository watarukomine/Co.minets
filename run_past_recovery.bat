@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   [Cominets] Past Data Full Recovery Batch (v2.3)
echo   Target Period: 2019/04/01 ~ 2026/06/07 (All 2,700 Patterns)
echo ============================================================
echo.

rem Delete missing_patterns.json to force all 2,700 patterns
rem if exist missing_patterns.json del missing_patterns.json

rem Ask user for clean start (only on first run, select N if resuming)
choice /c yn /t 60 /d n /m "Clean start (delete previous temp downloads)? [Resuming? Select N]"

rem Use single line syntax to prevent bracket parsing crash in command prompt
if %errorlevel% equ 1 echo [INFO] Cleaning up temp directory (extracted_data_temp)...
if %errorlevel% equ 1 del /q /f "extracted_data_temp" 2>nul
if %errorlevel% equ 2 echo [INFO] Resuming. Skipping cleanup...

echo.
echo [INFO] Checking required libraries...
echo ------------------------------------------------------------
python -c "import selenium, win32com, requests, google.oauth2" 2>nul
if errorlevel 1 (
    echo Required libraries [selenium, pywin32, requests, google-auth] are missing.
    echo Installing...
    python -m pip install selenium pywin32 requests google-auth
    if errorlevel 1 (
        echo [ERROR] Installation failed.
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Starting Edge browser on debug port 9222...
echo.
start "" launch_edge.bat
timeout /t 5 >nul

echo.
echo ------------------------------------------------------------
echo [STEP 1/4] QuickSight Date Filter Setting (2019/04/01 ~ 2026/06/07)...
echo ------------------------------------------------------------
python step_1_date_past_recovery.py auto
if %ERRORLEVEL% neq 0 (
    set "ERROR_MSG=Step 1: 日付フィルターの設定失敗 (step_1_date_past_recovery.py)"
    goto :error_exit
)

echo.
echo ------------------------------------------------------------
echo [STEP 2/4] RPA Data Extraction (All 2,700 patterns)...
echo ------------------------------------------------------------
python rpa_extractor_past_recovery.py
if %ERRORLEVEL% neq 0 (
    set "ERROR_MSG=Step 2: RPAデータ抽出の失敗 (rpa_extractor_past_recovery.py)"
    goto :error_exit
)

echo.
echo ------------------------------------------------------------
echo [STEP 3/4] Merging Past Data into Master ZIPs...
echo ------------------------------------------------------------
python merge_monthly_data.py
if %ERRORLEVEL% neq 0 (
    set "ERROR_MSG=Step 3: データマージ処理の失敗 (merge_monthly_data.py)"
    goto :error_exit
)

echo.
echo ------------------------------------------------------------
echo [STEP 4/4] Processing Data and Syncing to Firestore (Full Sync)...
echo ------------------------------------------------------------
python process_data.py --consolidate
if %ERRORLEVEL% neq 0 (
    set "ERROR_MSG=Step 4: Firestoreへのクラウド同期失敗 (process_data.py)"
    goto :error_exit
)

echo.
echo ------------------------------------------------------------
echo [STEP 5/5] Sending Completion Report Mail...
echo ------------------------------------------------------------
python send_recovery_report_mail.py
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Failed to send completion mail.
)

echo.
echo ============================================================
echo   [FINISHED] Past data recovery successfully completed.
echo ============================================================
pause
exit /b 0

:error_exit
echo.
echo ============================================================
echo   [ERROR] Batch process stopped due to an error.
echo   Reason: %ERROR_MSG%
echo ============================================================
echo.
echo Sending error report mail...
python send_recovery_report_mail.py error "%ERROR_MSG%"
pause
exit /b 1
