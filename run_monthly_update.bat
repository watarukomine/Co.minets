@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   【Cominets】月次データ更新バッチ (Ver 2.3 - 自動運転対応)
echo ============================================================
echo.
echo ------------------------------------------------------------
echo [準備] 必要なライブラリを確認中...
echo ------------------------------------------------------------
python -c "import selenium, win32com, requests, google.oauth2" 2>nul
if errorlevel 1 (
    echo 必要なライブラリ [selenium, pywin32, requests, google-auth] が不足しています。
    echo 自動インストールを開始します [数分かかる場合があります] ...
    python -m pip install selenium pywin32 requests google-auth
    if errorlevel 1 (
        echo [エラー] ライブラリのインストールに失敗しました。
        echo インターネット接続を確認するか、コマンドプロンプトで手動で「pip install selenium pywin32 requests google-auth」を実行してください。
        pause
        exit /b 1
    )
    echo ライブラリのインストールが完了しました。
)

echo.
echo ※Edgeデバッグポート 9222 を自動起動します。
echo.

start "" launch_edge.bat
timeout /t 5 >nul

set "RUN_MODE=auto"
set "TARGET_MONTH="

choice /c yn /t 10 /d n /m "対象年月を手動で指定（または対話操作）しますか？ (10秒後に自動的に「N (自動運転)」で進みます)"
if %errorlevel% equ 1 (
    set "RUN_MODE=manual"
    set /p TARGET_MONTH="対象年月を入力してください (例: 2026/05) [未入力で前月]: "
)

echo.
echo ------------------------------------------------------------
echo [STEP 1/4] QuickSightの日付フィルターを設定中...
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

echo.
echo ------------------------------------------------------------
echo [STEP 2/4] RPAデータ抽出を開始（一時フォルダへのダウンロード）...
echo ------------------------------------------------------------
python rpa_extractor_monthly.py
if %ERRORLEVEL% neq 0 goto ERR_EXTRACT

echo.
echo ------------------------------------------------------------
echo [STEP 3/4] 抽出データと過去データのマージ（結合）を行います...
echo ------------------------------------------------------------
python merge_monthly_data.py
if %ERRORLEVEL% neq 0 goto ERR_MERGE

echo.
echo ------------------------------------------------------------
echo [STEP 4/4] データの解析およびFirestoreへの同期を行います...
echo ------------------------------------------------------------
python process_data.py
if %ERRORLEVEL% neq 0 goto ERR_SYNC

echo.
echo ------------------------------------------------------------
echo [報告] 実行結果レポートをメール送信中...
echo ------------------------------------------------------------
python send_report_mail.py

echo.
echo ============================================================
echo   正常終了: すべてのプロセスが正常に完了しました！
echo ============================================================
goto END

:ERR_DATE
echo [ERROR] 日付設定に失敗しました。処理を中断します。
goto ERR_PAUSE

:ERR_EXTRACT
echo [ERROR] データ抽出に失敗しました。処理を中断します。
python send_report_mail.py
goto ERR_PAUSE

:ERR_MERGE
echo [ERROR] データマージに失敗しました。一時フォルダを確認してください。
python send_report_mail.py
goto ERR_PAUSE

:ERR_SYNC
echo [ERROR] Firestore同期に失敗しました。
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
