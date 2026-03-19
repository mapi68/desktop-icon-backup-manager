@echo off
rem ============================================================
rem  run_update_translations.cmd
rem
rem  Launcher for update_translations.ps1
rem
rem  Windows blocks unsigned PowerShell scripts by default.
rem  This file runs the .ps1 with -ExecutionPolicy Bypass so
rem  no system policy change is required.
rem
rem  Usage: double-click this file or run it from the terminal.
rem  Both files must be in the same folder.
rem ============================================================
powershell.exe -ExecutionPolicy Bypass -File "%~dp0update_translations.ps1"
