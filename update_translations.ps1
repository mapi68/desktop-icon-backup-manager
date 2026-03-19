#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$i18nPath = "i18n"

# ── Helper: colored output ────────────────────────────────────────────────────
function Write-Header { param($msg) Write-Host "`n$('=' * 60)`n $msg`n$('=' * 60)" -ForegroundColor Cyan }
function Write-Ok     { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warn   { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Err    { param($msg) Write-Host $msg -ForegroundColor Red }

Clear-Host
Write-Header "Translation Update Process"

# ── Create new locale file? ───────────────────────────────────────────────────
$newLocale = Read-Host "Create a new locale file? Enter locale code (e.g. it_IT) or leave blank to skip"
if ($newLocale -ne '') {
    $newFile = Join-Path $i18nPath "$newLocale.ts"
    if (Test-Path $newFile) {
        Write-Warn "  WARNING: $newFile already exists, skipping creation."
    } else {
        Write-Host "  Creating: $newFile"
        & pylupdate6.exe . -ts $newFile
        if ($LASTEXITCODE -ne 0) { Write-Err "  ERROR: Failed to create $newFile"; Read-Host; exit 1 }
        Write-Ok "  Done: $newFile created successfully."
    }
}

# ── --no-obsolete flag? ───────────────────────────────────────────────────────
$noObsolete = $null
$choice = Read-Host "`nUse --no-obsolete flag? Removes unused strings from .ts files [Y/n/c to cancel]"
switch -Regex ($choice.ToLower()) {
    '^c$' { Write-Host "  Cancelled by user."; Read-Host; exit 0 }
    '^n$' { Write-Host "  Option: obsolete strings will be KEPT" }
    default {
        $noObsolete = '--no-obsolete'
        Write-Host "  Option: obsolete strings will be REMOVED"
    }
}

# ── Collect .ts files ─────────────────────────────────────────────────────────
$tsFiles = Get-ChildItem -Path $i18nPath -Filter "*.ts" | Sort-Object Name
if ($tsFiles.Count -eq 0) { Write-Err "No .ts files found in '$i18nPath'"; Read-Host; exit 1 }

# Results table: locale -> hashtable of data
$results = [ordered]@{}
foreach ($f in $tsFiles) {
    $results[$f.BaseName] = @{
        Update   = '?'
        Compile  = '?'
        Finished = '?'
        Unfinished = '?'
    }
}

# ── STEP 1: pylupdate6 ────────────────────────────────────────────────────────
Write-Header "[1/2] Updating source strings..."
foreach ($f in $tsFiles) {
    Write-Host "  Updating: $($f.Name)"
    $args = @('.')
    if ($noObsolete) { $args += $noObsolete }
    $args += @('-ts', "$i18nPath/$($f.Name)")
    & pylupdate6.exe @args
    $results[$f.BaseName].Update = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'ERROR' }
}

# ── STEP 2: pyside6-lrelease ──────────────────────────────────────────────────
Write-Header "[2/2] Compiling binary files..."
foreach ($f in $tsFiles) {
    Write-Host "  Compiling: $($f.Name)"
    $output = & pyside6-lrelease.exe "$i18nPath/$($f.Name)" 2>&1
    Write-Host ($output | Out-String).TrimEnd()

    $results[$f.BaseName].Compile = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'ERROR' }

    # Parse: "Generated 336 translation(s) (336 finished and 0 unfinished)"
    $line = $output | Where-Object { $_ -match 'finished and' } | Select-Object -First 1
    if ($line -match '\((\d+) finished and (\d+) unfinished\)') {
        $results[$f.BaseName].Finished   = [int]$Matches[1]
        $results[$f.BaseName].Unfinished = [int]$Matches[2]
    }
}

# ── SUMMARY ───────────────────────────────────────────────────────────────────
Write-Header "SUMMARY"

$header = "  {0,-12}  {1,-8}  {2,-8}  {3,9}  {4,10}" -f "Locale", "Update", "Compile", "Finished", "Unfinished"
$divider = "  {0,-12}  {1,-8}  {2,-8}  {3,9}  {4,10}" -f ("-" * 12), ("-" * 8), ("-" * 8), ("-" * 9), ("-" * 10)
Write-Host $header
Write-Host $divider

$updateErrors  = 0
$compileErrors = 0
$warnings      = 0

foreach ($locale in $results.Keys) {
    $r   = $results[$locale]
    $uf  = $r.Unfinished
    $row = "  {0,-12}  {1,-8}  {2,-8}  {3,9}  {4,10}" -f $locale, $r.Update, $r.Compile, $r.Finished, $uf

    if ($r.Update  -eq 'ERROR') { $updateErrors++ }
    if ($r.Compile -eq 'ERROR') { $compileErrors++ }

    if ($r.Update -eq 'ERROR' -or $r.Compile -eq 'ERROR') {
        Write-Err $row
    } elseif ($uf -ne '?' -and [int]$uf -gt 0) {
        $warnings++
        Write-Warn "$row   <<< MISSING TRANSLATIONS"
    } else {
        Write-Ok $row
    }
}

Write-Host $divider
Write-Host ""

if ($updateErrors  -gt 0) { Write-Err   "  Update errors  : $updateErrors file(s)" }
if ($compileErrors -gt 0) { Write-Err   "  Compile errors : $compileErrors file(s)" }
if ($warnings      -gt 0) { Write-Warn  "  Missing transl.: $warnings file(s)" }

Write-Host ""
if ($updateErrors -eq 0 -and $compileErrors -eq 0) {
    if ($warnings -eq 0) {
        Write-Ok  "  Result: all $($tsFiles.Count) file(s) completed successfully."
    } else {
        Write-Warn "  Result: $($tsFiles.Count) file(s) processed - $warnings with missing translations."
    }
} else {
    Write-Err "  Result: $($tsFiles.Count) file(s) processed - check errors above."
}

Write-Host "`n$('=' * 60)`n"
