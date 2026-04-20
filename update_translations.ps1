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

# ── --no-obsolete flag? ───────────────────────────────────────────────────────
$noObsolete = $null
do {
    $choice = Read-Host "Use --no-obsolete flag? Removes unused strings from .ts files [Y/n/c to cancel]"
    $choiceLower = $choice.ToLower()
    $validChoice = $choiceLower -in @('y', 'n', 'c', '')
    if (-not $validChoice) { Write-Warn "  Invalid input. Please enter Y, n, or c." }
} while (-not $validChoice)

switch ($choiceLower) {
    'c'     { Write-Host "  Cancelled by user."; Read-Host; exit 0 }
    'n'     { Write-Host "  Option: obsolete strings will be KEPT" }
    default {
        $noObsolete = '--no-obsolete'
        Write-Host "  Option: obsolete strings will be REMOVED"
    }
}

# ── Collect .ts files ─────────────────────────────────────────────────────────
$allTsFiles = Get-ChildItem -Path $i18nPath -Filter "*.ts" | Sort-Object Name
if ($allTsFiles.Count -eq 0) { Write-Err "No .ts files found in '$i18nPath'"; Read-Host "Press ENTER to exit"; exit 1 }

# ── Filter by locale? ─────────────────────────────────────────────────────────
$availableCodes = ($allTsFiles | ForEach-Object { $_.BaseName }) -join ', '
Write-Host "`nAvailable locales: $availableCodes"
$localeFilter = Read-Host "Process only specific locale(s)? Enter one or more codes separated by commas, or leave blank for ALL"

$localeFilterList = @()
if ($localeFilter -ne '') {
    $localeFilterList = @($localeFilter -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' })
    $notFound = @($localeFilterList | Where-Object { -not (Test-Path (Join-Path $i18nPath "$_.ts")) })
    if ($notFound.Count -gt 0) {
        Write-Err "  ERROR: The following locale(s) were not found: $($notFound -join ', ')"
        Read-Host "Press ENTER to exit"
        exit 1
    }
    Write-Host "  Filter: $($localeFilterList -join ', ') will be processed."
} else {
    Write-Host "  Filter: ALL locales will be processed."
}

# ── Create new locale file? ───────────────────────────────────────────────────
$newLocale = Read-Host "`nCreate a new locale file? Enter locale code (e.g. en_US) or leave blank to skip"
if ($newLocale -ne '') {
    $newFile = Join-Path $i18nPath "$newLocale.ts"
    if (Test-Path $newFile) {
        Write-Warn "  WARNING: $newFile already exists, skipping creation."
    } else {
        Write-Host "  Creating: $newFile"
        & pylupdate6.exe . -ts $newFile
        if ($LASTEXITCODE -ne 0) { Write-Err "  ERROR: Failed to create $newFile"; Read-Host "Press ENTER to exit"; exit 1 }
        Write-Ok "  Done: $newFile created successfully."
    }
}

# ── Apply locale filter ───────────────────────────────────────────────────────
if ($localeFilterList.Count -gt 0) {
    $tsFiles = $allTsFiles | Where-Object { $localeFilterList -contains $_.BaseName }
} else {
    $tsFiles = $allTsFiles
}

# ── Auto-include newly created locale if not already in selection ─────────────
if ($newLocale -ne '') {
    $alreadyIncluded = $tsFiles | Where-Object { $_.BaseName -eq $newLocale }
    if (-not $alreadyIncluded) {
        $newLocaleFile = Get-ChildItem -Path $i18nPath -Filter "$newLocale.ts" -ErrorAction SilentlyContinue
        if ($newLocaleFile) {
            Write-Warn "  NOTE: Newly created locale '$newLocale' added to processing list."
            $tsFiles = @($tsFiles) + @($newLocaleFile) | Sort-Object Name
        }
    }
}

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

$startTime = Get-Date

# ── STEP 1: pylupdate6 ────────────────────────────────────────────────────────
Write-Header "[1/2] Updating source strings..."
foreach ($f in $tsFiles) {
    Write-Host "  Updating: $($f.Name)"
    $cmdArgs = @('.')
    if ($noObsolete) { $cmdArgs += $noObsolete }
    $cmdArgs += @('-ts', (Join-Path $i18nPath $f.Name))
    & pylupdate6.exe @cmdArgs
    $results[$f.BaseName].Update = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'ERROR' }

    if ($results[$f.BaseName].Update -eq 'ERROR') {
        Write-Warn "  WARNING: Update failed for $($f.Name) - skipping compile step for this file."
    }
}

# ── STEP 2: pyside6-lrelease ──────────────────────────────────────────────────
Write-Header "[2/2] Compiling binary files..."
foreach ($f in $tsFiles) {
    if ($results[$f.BaseName].Update -eq 'ERROR') {
        Write-Warn "  Skipping compile for $($f.Name) due to update error."
        $results[$f.BaseName].Compile = 'SKIPPED'
        continue
    }

    Write-Host "  Compiling: $($f.Name)"

    # Capture all output (stdout and stderr) as strings
    $rawOutput = & pyside6-lrelease.exe (Join-Path $i18nPath $f.Name) 2>&1

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

        # Match "Ignored 25 untranslated"
        if ($l -match 'Ignored\s+(\d+)\s+untranslated') {
            $unf += [int]$Matches[1]
        }
    }

    $results[$f.BaseName].Finished   = $fin
    $results[$f.BaseName].Unfinished = $unf
}

# ── SUMMARY ───────────────────────────────────────────────────────────────────
Write-Header "SUMMARY"

$elapsed = (Get-Date) - $startTime
$elapsedStr = '{0:mm\:ss}' -f $elapsed

if ($localeFilterList.Count -gt 0) {
    Write-Host "  Locale filter : $($localeFilterList -join ', ')"
} else {
    Write-Host "  Locale filter : ALL"
}
Write-Host "  Elapsed time  : $elapsedStr"
Write-Host ""

$fmt = "  {0,-12}  {1,-8}  {2,-8}  {3,9}  {4,10}"
Write-Host ($fmt -f "Locale", "Update", "Compile", "Finished", "Unfinished")
Write-Host ($fmt -f ("-" * 12), ("-" * 8), ("-" * 8), ("-" * 9), ("-" * 10))

$errU = 0; $errC = 0; $warns = 0
$totalFin = 0; $totalUnf = 0

foreach ($locale in $results.Keys) {
    $r = $results[$locale]
    $row = $fmt -f $locale, $r.Update, $r.Compile, $r.Finished, $r.Unfinished

    if ($r.Update -eq 'ERROR') { $errU++ }
    if ($r.Compile -eq 'ERROR') { $errC++ }
    $totalFin += $r.Finished
    $totalUnf += $r.Unfinished

    if ($r.Update -eq 'ERROR' -or $r.Compile -eq 'ERROR') {
        Write-Err $row
    } elseif ($r.Unfinished -gt 0) {
        $warns++
        Write-Warn "$row   <<< UNTRANSLATED"
    } else {
        Write-Ok $row
    }
}

Write-Host ($fmt -f ("-" * 12), ("-" * 8), ("-" * 8), ("-" * 9), ("-" * 10))
Write-Host ($fmt -f "TOTAL", "", "", $totalFin, $totalUnf)
Write-Host ""

if ($errU -gt 0) { Write-Err "  Update errors   : $errU file(s)" }
if ($errC -gt 0) { Write-Err "  Compile errors  : $errC file(s)" }
if ($warns -gt 0) { Write-Warn "  Untranslated    : $warns file(s)" }

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
