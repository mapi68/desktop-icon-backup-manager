@echo off
setlocal enabledelayedexpansion
cls

rem Define the path for translation files
set "i18nPath=i18n"

echo ============================================================
echo  Translation Update Process
echo ============================================================
echo.

rem 1. Run pylupdate6 for each file to sync with source code
echo [1/2] Updating source strings...
echo.
for %%f in ("%i18nPath%\*.ts") do (
    echo   Updating: %%~nxf
    pylupdate6.exe --no-obsolete . -ts "%i18nPath%/%%~nxf"
)

echo.
echo ============================================================
echo.

rem 2. Run pyside6-lrelease to compile .ts into .qm binary files
echo [2/2] Compiling binary files...
echo.
for %%f in ("%i18nPath%\*.ts") do (
    echo   Compiling: %%~nxf
    pyside6-lrelease.exe "%i18nPath%/%%~nxf"
)

echo.
echo ============================================================
echo  Process completed successfully!
echo ============================================================
echo.
pause
endlocal
