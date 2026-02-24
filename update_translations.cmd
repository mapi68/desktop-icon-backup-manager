@echo off
setlocal enabledelayedexpansion

rem Define the path for translation files
set "i18nPath=i18n"

echo Starting translation update process...

rem 1. Run pylupdate6 for each file to sync with source code
for %%f in ("%i18nPath%\*.ts") do (
    echo Updating source strings for: %%~nxf
    pylupdate6.exe --no-obsolete . -ts "%i18nPath%/%%~nxf"
)

rem 2. Run pyside6-lrelease to compile .ts into .qm binary files
for %%f in ("%i18nPath%\*.ts") do (
    echo Compiling binary file for: %%~nxf
    pyside6-lrelease.exe "%i18nPath%/%%~nxf"
)

echo Process completed successfully!
endlocal
