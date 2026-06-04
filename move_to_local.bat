@echo off
pushd "%~dp0"

set "dst=%USERPROFILE%\Desktop\rpa_downloads"
if not exist "%dst%" mkdir "%dst%"

echo --- Moving RPA Downloads to Local Desktop ---

echo Moving from .\downloads...
if exist "downloads" (
    move "downloads\*.csv" "%dst%\"
) else (
    echo [SKIP] 'downloads' folder not found in %CD%
)

echo.
echo Moving from .\downloads_egz100...
if exist "downloads_egz100" (
    move "downloads_egz100\*.csv" "%dst%\"
)

echo.
echo SUCCESS: Process completed.
echo If Fileforce warning persists, right-click Fileforce icon and "Purge Cache".
echo.
popd
pause
