#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$i18nPath = "i18n"

# ── Helpers: colored output ───────────────────────────────────────────────────
function Write-Header { param($msg) Write-Host "`n$('=' * 60)`n $msg`n$('=' * 60)" -ForegroundColor Cyan }
function Write-Ok     { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Warn   { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Err    { param($msg) Write-Host $msg -ForegroundColor Red }

Clear-Host
Write-Header "Translation Update Process"

# ── Create new locale file? ───────────────────────────────────────────────────
$newLocale = Read-Host "Create a new locale file? Enter locale code (e.g. en_US) or leave blank to skip"
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

# Results table initialization
$results = [ordered]@{}
foreach ($f in $tsFiles) {
    $results[$f.BaseName] = @{
        Update     = '?'
        Compile    = '?'
        Finished   = 0
        Unfinished = 0
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

    # Capture all output (stdout and stderr) as strings
    $rawOutput = & pyside6-lrelease.exe "$i18nPath/$($f.Name)" 2>&1

    $results[$f.BaseName].Compile = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'ERROR' }

    $fin = 0
    $unf = 0

    foreach ($line in $rawOutput) {
        $l = $line.ToString().Trim()
        if ([string]::IsNullOrWhiteSpace($l)) { continue }
        Write-Host "    $l"

        # Match "336 finished"
        if ($l -match '(\d+)\s+finished') {
            $fin = [int]$Matches[1]
        }

        # Match "0 unfinished"
        if ($l -match '(\d+)\s+unfinished') {
            $unf += [int]$Matches[1]
        }

        # Match "Ignored 25 untranslated" (This solves your specific issue)
        if ($l -match 'Ignored\s+(\d+)\s+untranslated') {
            $unf += [int]$Matches[1]
        }
    }

    $results[$f.BaseName].Finished   = $fin
    $results[$f.BaseName].Unfinished = $unf
}

# ── SUMMARY ───────────────────────────────────────────────────────────────────
Write-Header "SUMMARY"

$fmt = "  {0,-12}  {1,-8}  {2,-8}  {3,9}  {4,10}"
Write-Host ($fmt -f "Locale", "Update", "Compile", "Finished", "Unfinished")
Write-Host ($fmt -f ("-" * 12), ("-" * 8), ("-" * 8), ("-" * 9), ("-" * 10))

$errU = 0; $errC = 0; $warns = 0

foreach ($locale in $results.Keys) {
    $r = $results[$locale]
    $row = $fmt -f $locale, $r.Update, $r.Compile, $r.Finished, $r.Unfinished

    if ($r.Update -eq 'ERROR') { $errU++ }
    if ($r.Compile -eq 'ERROR') { $errC++ }

    if ($r.Update -eq 'ERROR' -or $r.Compile -eq 'ERROR') {
        Write-Err $row
    } elseif ($r.Unfinished -gt 0) {
        $warns++
        Write-Warn "$row   <<< UNTRANSLATED"
    } else {
        Write-Ok $row
    }
}

Write-Host ("  " + ("-" * 53))
Write-Host ""

if ($errU -gt 0) { Write-Err "  Update errors: $errU file(s)" }
if ($errC -gt 0) { Write-Err "  Compile errors: $errC file(s)" }
if ($warns -gt 0) { Write-Warn "  Untranslated: $warns file(s)" }

Write-Host ""
if ($errU -eq 0 -and $errC -eq 0) {
    if ($warns -eq 0) {
        Write-Ok "  Success. All files are 100% translated."
    } else {
        Write-Warn "  Completed, but $warns file(s) have missing translations."
    }
} else {
    Write-Err "  Process failed with errors. Check table above."
}

Write-Host "`n$('=' * 60)`n"