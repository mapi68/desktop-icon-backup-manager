<!-- SEO Schema Markup (Hidden) -->
<!--
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Desktop Icon Backup Manager",
  "description": "Free, open-source Windows utility to save and restore desktop icon positions with live visual preview, adaptive scaling, and multi-monitor support",
  "applicationCategory": "UtilitiesApplication",
  "operatingSystem": ["Windows 7", "Windows 8", "Windows 10", "Windows 11"],
  "downloadUrl": "https://github.com/mapi68/desktop-icon-backup-manager/releases",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  },
  "license": "https://opensource.org/licenses/MIT",
  "creator": {
    "@type": "Person",
    "name": "mapi68"
  },
  "sourceCodeRepository": "https://github.com/mapi68/desktop-icon-backup-manager"
}
-->

# Desktop Icon Backup Manager — Save, Restore & Manage Windows Desktop Icon Positions

<div align="center">

[![☕ Buy me a coffee](https://img.shields.io/badge/Support%20Us-Buy%20a%20Coffee-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/mapi68)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Windows 7, 8, 10, 11](https://img.shields.io/badge/Windows-7%20%7C%208%20%7C%2010%20%7C%2011-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)

[![Latest Release](https://img.shields.io/github/v/release/mapi68/desktop-icon-backup-manager?style=for-the-badge&logo=github&color=2ea44f)](https://github.com/mapi68/desktop-icon-backup-manager/releases)
[![Total Downloads](https://img.shields.io/github/downloads/mapi68/desktop-icon-backup-manager/total?style=for-the-badge&logo=github-actions&color=6f42c1)](https://github.com/mapi68/desktop-icon-backup-manager/releases)

[![MIT License](https://img.shields.io/badge/License-MIT-41AD49?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)
[![Actively Maintained](https://img.shields.io/badge/Maintained-Yes-green?style=for-the-badge&logo=github)](https://github.com/mapi68/desktop-icon-backup-manager/graphs/commit-activity)

</div>

---

## Quick Overview

**Desktop Icon Backup Manager** is the most feature-complete, free, open-source tool for **saving and restoring desktop icon positions on Windows 7, 8, 10, and 11**. It's the only solution offering a **live visual diff preview before restoration**, **automatic adaptive scaling for resolution changes**, **comprehensive multi-monitor support**, and **full command-line automation** — packaged in a single portable `.exe` requiring no installation.

> **TL;DR:** Windows keeps rearranging your desktop icons without warning. This tool saves your exact layout and restores it instantly—with a color-coded preview showing exactly what will change. **Free. Open Source. Portable. No installation needed.**

---

## Does Your Desktop Icon Layout Keep Changing? You're Not Alone

Windows has had a well-documented bug since Windows 7 that persists through Windows 11 (including the latest 25H2 version): **desktop icons spontaneously rearrange themselves** without user action. This frustrating issue affects millions of Windows users daily.

### Common Triggers for Desktop Icon Rearrangement:

- 🔄 **After Windows Updates** — Icons reset to the left side, auto-sort alphabetically, or redistribute randomly
- 🖥️ **After Connecting/Disconnecting External Monitors** — Entire layout collapses onto the primary display when external monitors are disconnected
- 🎮 **After Playing Full-Screen Games** — Games change resolution on launch/exit, causing Windows to scramble all icon positions
- 💤 **After Sleep, Hibernation, or Lock Screen** — Icons shift position, especially along the right edge of the desktop
- 🔌 **After Changing Screen Resolution or DPI** — Icons pile up in the top-left corner or become inaccessible
- 📺 **After Switching Between Displays** — Moving from laptop screen to external TV or projector completely disrupts the layout
- 🔁 **After System Reboot** — Windows ignores carefully arranged positions and auto-arranges instead

**Desktop Icon Backup Manager is the definitive solution.** Save your perfect desktop layout in one click. Restore it in seconds whenever Windows moves icons around—and see a color-coded preview of every change before you commit.

---

## 📖 Complete Documentation

[![Download User Manual](https://img.shields.io/badge/📖%20Full%20Manual-PDF%20Download-EC1C24?style=for-the-badge&logo=adobe-acrobat-reader&logoColor=white)](https://mapi68.github.io/desktop-icon-backup-manager/manual.pdf)

> **Complete documentation, tutorial videos, and advanced guides** are available in the [Desktop Icon Backup Manager User Manual (PDF)](https://mapi68.github.io/desktop-icon-backup-manager/manual.pdf)

---

## Why Desktop Icon Backup Manager Stands Apart

While other icon layout tools simply save coordinates and restore them, **Desktop Icon Backup Manager goes far beyond basic functionality** with advanced features you won't find in competing tools.

### 🔍 Live Diff Preview — A Unique Feature

Before restoring any backup, you see a **real-time, color-coded visual overlay** showing **exactly which icons will move**, which are already in the correct position, and which exist in the backup but are missing from your current desktop.

**No other free Windows desktop icon tool offers this feature.** You always know precisely what will happen before clicking Restore—eliminating surprises and accidental icon movement.

#### Color Legend:
| Indicator | Meaning |
|-----------|---------|
| 🔵 **Blue (soft halo)** | Already in correct position — **will not move** |
| 🟠 **Orange** → 🔴 **Red** | **Will move** — orange shows current position, red shows saved destination |
| 🟢 **Green** | Exists in backup but **not currently on desktop** — will be skipped |

### 🔄 Adaptive Scaling for Resolution Changes

Restoring a backup from a 1920×1080 monitor onto a 2560×1440 display? **Icon positions are automatically recalculated proportionally**, so they land in the correct area of your new screen. Icons no longer pile up in corners when resolution changes—this includes DPI scaling differences.

**Works seamlessly across:**
- Different resolution changes (1080p ↔ 1440p ↔ 4K)
- DPI scaling differences (100% ↔ 125% ↔ 150%)
- Multiple monitor configurations

### ⚖️ Compare Any Two Backups

Go beyond "current vs. latest backup." **Compare any two saved layouts side-by-side** to see exactly which icons were added, removed, or repositioned between snapshots. Track how your desktop evolved over time, or choose the best snapshot from multiple old backups.

### 🖥️ Multi-Monitor Awareness & Configuration Detection

Every backup records complete monitor configuration: count, resolution, and physical arrangement. When restoring on a different setup, **the app warns you automatically** before proceeding.

**Create named backups for each configuration:**
- `Laptop Only` — for standalone laptop use
- `Office Dock` — for docked configuration with external monitors
- `Home Dual Monitor` — for home office setup
- Switch between configurations instantly with a single click

### ⚡ Full Command-Line Automation

Run backup and restore operations **silently from the command line**, Windows Task Scheduler, login scripts, or batch files with no GUI. Schedule **automatic desktop icon backups at Windows login**—your layout is always safe without manual intervention.

```bash
# Silent backup to background
desktop-icon-backup-manager.exe --backup --silent

# Silent restore of latest layout
desktop-icon-backup-manager.exe --restore latest --silent
```

### 🔓 Completely Open Source (MIT Licensed)

**Every line of code** is publicly available on GitHub under the MIT license—auditable, transparent, and forkable. No telemetry, no ads, no accounts, no cloud services. Your backup files are plain JSON text—human-readable and portable between machines.

---

## Complete Feature List

### Core Features — Save & Restore Desktop Icon Layouts

- **💾 One-Click Quick Backup** — Save entire desktop icon layout instantly with optional descriptive tag (`Before Windows Update`, `Dual Monitor Setup`, etc.)
- **↺ One-Click Restore** — Restore icon positions from the latest backup or pick any snapshot from your backup history
- **🏷️ Custom Tags & Descriptions** — Label each backup with meaningful names for easy identification and organization
- **📋 Quick-Access Profiles Dropdown** — 14 pre-made profile names for instant tagging:
  - *Work, Gaming, Presentation, Dev/Coding, Meeting, Home, Office, Laptop, Docked/External Monitor, Clean Desktop, Pre-Update, Pre-Reboot, Favorite, Test*
  - One-click selection pre-fills the tag field; edit further if needed
- **📊 Complete Metadata Tracking** — Every backup records screen resolution, DPI scaling, monitor count, and arrangement

### Advanced Features — What Sets This Tool Apart

- **🔍 Live Diff Preview** — Real-time color-coded overlay showing exactly what will move before restore *(unique feature)*
- **🖼️ Visual Dot-Map Layout Preview** — Mini-map visualization of all icon positions with hover tooltips
- **🔄 Adaptive Scaling** — Proportional position recalculation when restoring to different resolution or DPI *(unique feature)*
- **🖥️ Multi-Monitor Full Support** — Save/restore across any monitor configuration with automatic mismatch warnings
- **⚖️ Backup Comparison Tool** — Diff any two saved layouts side-by-side *(unique feature)*
- **✏️ Inline Tag Editing** — Double-click backup tags in the table to rename instantly—no dialog boxes
- **📤 Export Backups** — Export selected or all backups to ZIP archive or folder for backup, sharing, or off-site storage
- **📥 Import Backups** — Import `.json` backup files or ZIP archives from other machines—duplicates safely skipped
- **🗑️ Smart Auto-Cleanup** — Automatically manage backup count (keep 5, 10, 25, 50, or unlimited most recent)
- **⚡ System Tray Integration** — Save or restore silently from taskbar tray icon without opening main window

### Automation & Command-Line (CLI) Features

- **Auto-Save on Exit** — Automatically backup desktop icon positions every time the application closes
- **Auto-Restore on Startup** — Automatically restore latest layout every time Windows starts
- **🔔 Automatic Update Checker** — Check GitHub for new versions at startup with one-click download; also available manually via Help menu
- **Command Line Interface (CLI)** — Full `--backup`, `--restore`, `--silent` support for scripting, Task Scheduler, and batch automation
- **Non-Blocking Threads** — Save/restore operations never freeze the UI; live progress indicator always visible

### Usability & User Experience

- **📋 Sortable & Filterable Backup Table** — Sort backups by tag, resolution, icon count, or timestamp; real-time search filtering
- **🎨 Color-Coded Tag Bar** — Each unique tag gets a distinct color indicator on the left edge of backup rows—consistent tags always show same color for instant visual recognition
- **↔️ Fully Resizable Windows** — All windows adapt to any screen size, resolution, or DPI scaling
- **🌍 26 Language Support** — Auto-detected from Windows locale, manually selectable:
  - Arabic, Chinese (Simplified), Chinese (Traditional), Czech, Danish, Dutch, English, Finnish, French, German, Greek, Hindi, Italian, Japanese, Korean, Norwegian Bokmål, Polish, Portuguese (Brazil), Portuguese (Portugal), Romanian, Russian, Slovenian, Spanish, Swedish, Turkish, Ukrainian
- **⌨️ Full Keyboard Navigation** — All features accessible via keyboard shortcuts (see shortcuts table below)
- **📋 Timestamped Activity Log** — Complete operation history with timestamps; copy with `Ctrl+A`/`Ctrl+C`
- **🗒️ Persistent Log File** — Every operation silently logged to `history.log` (max 500 entries, auto-trimmed)
- **✅ Confirmation Dialogs** — Always confirms before overwrite or delete—no accidents

---

## Comparison: Desktop Icon Backup Manager vs Competitors

Desktop Icon Backup Manager is the most comprehensive solution. Here's how it compares to other available tools:

| Feature | **Desktop Icon Backup Manager** | ReIcon (Sordum) | DesktopOK | Windows Built-in |
|---------|:---:|:---:|:---:|:---:|
| **Save icon positions** | ✅ | ✅ | ✅ | ❌ |
| **Restore icon positions** | ✅ | ✅ | ✅ | ❌ |
| **Live visual diff preview** | ✅ | ❌ | ❌ | ❌ |
| **Visual dot-map preview** | ✅ | ❌ | ❌ | ❌ |
| **Compare any two backups** | ✅ | ❌ | ❌ | ❌ |
| **Inline tag editing** | ✅ | ❌ | ❌ | ❌ |
| **Color-coded tag indicators** | ✅ | ❌ | ❌ | ❌ |
| **Export/Import backups (ZIP & folder)** | ✅ | ❌ | ❌ | ❌ |
| **Adaptive scaling (resolution changes)** | ✅ | ✅ | ❌ | ❌ |
| **Multi-monitor support** | ✅ | ✅ | ✅ | ❌ |
| **CLI/Task Scheduler automation** | ✅ | ✅ | ❌ | ❌ |
| **Backup search & filtering** | ✅ | ❌ | ❌ | ❌ |
| **Auto-save on exit** | ✅ | ⚠️ partial | ✅ | ❌ |
| **Auto-restore on startup** | ✅ | ⚠️ via shortcut | ✅ | ❌ |
| **Automatic update checker** | ✅ | ❌ | ❌ | ❌ |
| **System tray integration** | ✅ | ✅ | ✅ | ❌ |
| **Open source (MIT license)** | ✅ | ❌ | ❌ | — |
| **Portable executable** | ✅ | ✅ | ✅ | — |
| **Windows 11 25H2 support** | ✅ | ✅ | ⚠️ | — |
| **Multi-language UI** | ✅ | ❌ | ✅ | — |
| **Free forever** | ✅ | ✅ | ✅ | — |

**Why the Differences Matter:**
- **ReIcon** is lightweight with CLI support but lacks visual previews, backup comparison, and search functionality
- **DesktopOK** is the oldest tool in this space but is closed-source, lacks CLI, offers no diff preview, and receives infrequent Windows 11 updates
- **Desktop Icon Backup Manager** is the only solution with live visual diff previews, cross-backup comparison, and an auditable open-source codebase

---

## System Requirements

- **Windows Versions:** Windows 7, 8, 10, or 11 (32-bit and 64-bit, including latest 25H2)
- **Python:** 3.8+ *only required if running from source code*; the `.exe` has zero external dependencies
- **Desktop Icons:** Must be visible (Right-click desktop → **View** → enable **Show desktop icons**)
- **Permissions:** No administrator rights required—runs as standard user

---

## Getting Started — Installation & Setup

### Option 1: Download Pre-Built Executable (Recommended)

No installation. No Python. No dependencies. Download, extract, and run.

1. Visit the [Releases page](https://github.com/mapi68/desktop-icon-backup-manager/releases)
2. Download the latest ZIP file
3. Extract to any folder (e.g., `C:\Tools\Desktop Icon Backup Manager\`)
4. Run `Desktop Icon Backup Manager.exe`
5. The `icon_backups` folder and `settings.ini` are created automatically on first run

**Syncing Across Multiple PCs with OneDrive (Advanced):**
- Create a folder in OneDrive: `C:\Users\YourName\OneDrive\DIBM\`
- Extract the ZIP into that OneDrive folder
- The `icon_backups` and `settings.ini` files automatically sync across all your Windows PCs
- Run the `.exe` from that OneDrive folder on each machine
- ⚠️ Avoid running simultaneously on multiple PCs to prevent file conflicts

### Option 2: Run from Source Code (Python)

```bash
git clone https://github.com/mapi68/desktop-icon-backup-manager.git
cd desktop-icon-backup-manager
pip install -r requirements.txt
python main.py
```

**Required Python Libraries:**
- `PyQt6` — GUI framework
- `pywin32` — Windows API access

---

## How to Use — Step-by-Step Guide

### Saving Your Desktop Icon Layout

1. *(Optional)* Type a descriptive tag in the text field—examples:
   - `Before Windows Update`
   - `Work Setup — Dual Monitors`
   - `Gaming Configuration`
   - Leave blank for default `Quick Backup` label

2. **Alternative:** Click the **📋 Profiles** dropdown to the right of the tag field
   - Choose one of 14 pre-made names (Work, Gaming, Presentation, Dev/Coding, Meeting, Home, Office, Laptop, Docked/External Monitor, Clean Desktop, Pre-Update, Pre-Reboot, Favorite, Test)
   - The selected name is instantly copied into the tag field
   - Edit further if needed, then save

3. Click **💾 SAVE QUICK BACKUP** button or press `Ctrl+S`

**Result:** A compact JSON snapshot (2–10 KB) containing all icon positions and screen metadata is saved to the `icon_backups` folder.

> **Note:** Pressing `Ctrl+S` always tags the backup as *"Quick Backup (Shortcut)"*. Use the button instead to save with custom tags.

### Restoring Your Desktop Icons

**Quick Restore (Latest Backup):**
- Click **↺ RESTORE LATEST** button
- Confirm the action in the dialog
- Icon positions are instantly restored to the saved layout

**Full Control (Choose Specific Backup):**
1. Click **↺ BACKUP MANAGER** button (or press `Ctrl+M`)
2. Browse your backup history, search by tag, or filter by resolution
3. **Preview the Live Diff** — see exactly which icons will move (orange → red), stay (blue), or be skipped (green)
4. Click **↺ Restore** to apply the selected layout

### Editing Backup Tags

In the Backup Manager window:
1. **Double-click** any tag in the first column of the backup table
2. **Edit the text inline** — type your new description
3. **Press Enter** to save or **Escape** to cancel
4. Changes are immediately written to the backup file

> **Note:** Double-clicking other columns (Resolution, Icon Count, Timestamp) opens the restore dialog as usual.

### Exporting Backups (Backup, Share, or Archive)

1. Open **↺ BACKUP MANAGER** (press `Ctrl+M`)
2. **Select backups** to export (or select all)
3. Click **📤 Export Backups...** button (or use **File → 📤 Export Backups...**)
4. Choose export format:
   - **ZIP Archive** — Single `.zip` file containing all selected backups
   - **Folder** — Copy `.json` files to a destination folder of your choice
5. Confirm location and export
6. **Success message** shows how many backups were exported

### Importing Backups (Restore from Another PC)

1. Open **↺ BACKUP MANAGER** (press `Ctrl+M`)
2. Click **📥 Import Backups...** button (or use **File → 📥 Import Backups...**)
3. **Select files:** Choose one or more `.json` backup files and/or `.zip` archives
4. The importer validates each file before importing
5. **Duplicate handling:** Files that already exist in `icon_backups` are automatically **skipped** (never overwritten)
6. **Summary dialog** shows: ✓ imported, ⏭️ skipped (already exist), and any errors

### Command-Line Automation (Advanced)

Silent backup and restore for scripts, Task Scheduler, and batch files:

```bash
# Silent backup — no window, exits immediately
desktop-icon-backup-manager.exe --backup --silent

# Restore the most recent layout silently
desktop-icon-backup-manager.exe --restore latest --silent

# Restore a specific saved layout by filename
desktop-icon-backup-manager.exe --restore "1920x1080_20241211_143015.json" --silent
```

**Exit Codes:** `0` = success, `1` = error

**Automatic Backup at Windows Login (Using Task Scheduler):**
1. Open **Windows Task Scheduler** (search from Start menu)
2. Create → **Create Basic Task**
3. **Name:** `Desktop Icon Auto-Backup`
4. **Trigger:** Select "When I log on"
5. **Action:** Start a program
   - Program: `C:\Path\To\desktop-icon-backup-manager.exe`
   - Arguments: `--backup --silent`
6. Click Finish
7. **From now on:** Your desktop icon layout is automatically backed up every time you log in

---

## Settings Reference & Configuration

### Available Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Start Minimized to Tray** | Launch application hidden with zero visual footprint; access via tray icon | `false` |
| **Auto-Save on Exit** | Automatically back up desktop icons every time the application closes | `false` |
| **Auto-Restore on Startup** | Automatically restore the latest icon layout every time Windows starts | `false` |
| **Enable Adaptive Scaling** | Recalculate icon positions proportionally when restoring to different resolution | `false` |
| **Minimize to Tray on Close** | Clicking the close (X) button hides to tray instead of quitting | `false` |
| **Check for Updates on Startup** | Automatically check GitHub for new version 10 seconds after launch | `true` |
| **Auto-Cleanup Limit** | Auto-delete oldest backups—keep 5, 10, 25, 50, or unlimited | `0` (unlimited) |

### Configuration File (settings.ini)

Settings are stored in `settings.ini` alongside the executable. Automatically created on first run. Edit with any text editor:

```ini
[General]
start_minimized=false
auto_save_on_exit=false
auto_restore_on_startup=false
check_updates_on_startup=true
adaptive_scaling_enabled=false
close_to_tray=false
cleanup_limit=0
geometry=@Rect(100 100 800 650)
```

Invalid values automatically reset to defaults on next launch.

> **⚠️ Warning:** Enabling both **Auto-Save on Exit** and **Auto-Restore on Startup** creates a cycle where any layout—even a broken one—gets saved and restored. If icons are already misaligned, use the Backup Manager to restore a known-good snapshot first.

---

## Keyboard Shortcuts

Quick reference for all keyboard commands:

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save quick backup |
| `Ctrl+M` | Open Backup Manager |
| `Ctrl+,` | Open Settings |
| `Ctrl+Q` | Exit application |
| `F1` | Open User Manual (PDF) |

---

## Backup File Format & Structure

Backups are stored as human-readable JSON text files in the `icon_backups` subfolder:

**Filename Format:** `{width}x{height}_{YYYYMMDD}_{HHMMSS}.json`

**Example:** `1920x1080_20241211_143015.json`

**File Structure Example:**
```json
{
    "timestamp": "2024-12-11T14:30:15.123456",
    "icon_count": 12,
    "description": "Work Setup — Dual Monitors",
    "display_metadata": {
        "monitor_count": 2,
        "primary_resolution": "1920x1080",
        "screens": [...]
    },
    "icons": {
        "This PC": [100, 200],
        "Recycle Bin": [100, 350],
        "Documents": [200, 200],
        "Downloads": [200, 350]
    }
}
```

**Why JSON Format?**
- Plain text — human-readable and auditable
- Portable — copy between machines easily
- Compact — 50 backups take less than 500 KB of storage
- Compatible — open with any text editor

---

## Frequently Asked Questions

### General Questions

**Can I rename a backup tag after saving?**
Yes — in the Backup Manager, double-click the tag cell in the first column to edit it directly in the table. Changes are saved to the `.json` file immediately.

**What are Profiles and how do I use them?**
Profiles is a dropdown menu next to the tag field containing 14 pre-made names (Work, Gaming, Presentation, Dev/Coding, Meeting, Home, Office, Laptop, Docked/External Monitor, Clean Desktop, Pre-Update, Pre-Reboot, Favorite, Test) to help you tag backups consistently. Select one and the name is instantly copied into the tag field—edit further if needed before saving. All profile names are fully translated to 26 supported languages.

**Can I transfer backups to another PC?**
Yes — use **📤 Export Backups...** in the Backup Manager to package backups as a ZIP archive or copy to a folder. On the target machine, use **📥 Import Backups...** to bring them in. Existing files are automatically skipped to prevent overwriting.

### Windows Issues & Troubleshooting

**Why do my desktop icons keep moving in Windows 11?**
This is a long-standing Windows bug that Microsoft has never fixed—it affects Windows 7, 10, and 11 (including 25H2). Windows silently changes screen resolution when you connect a monitor, start a game, wake from sleep, or install updates, causing icons to rearrange. Desktop Icon Backup Manager solves this by saving your layout and restoring it with one click whenever Windows moves icons.

**How do I prevent Windows from rearranging desktop icons?**
There is no built-in Windows setting that permanently prevents icon rearrangement. The most reliable solution is Desktop Icon Backup Manager: save your layout, restore it with one click after Windows moves things. Enable **Auto-Restore on Startup** to restore your layout automatically every Windows boot—no manual rearrangement ever needed again.

**My desktop icons moved after a Windows Update—how do I recover them?**
1. Open Desktop Icon Backup Manager
2. Click **Backup Manager** (or press `Ctrl+M`)
3. Look for the backup created before the update (check timestamps)
4. Click **↺ Restore**
5. If Auto-Save on Exit was enabled, a backup was automatically created when you last closed the app

**I want to preview what will change before restoring—how?**
This is a standout feature. Select any backup in the Backup Manager and the **live diff preview** shows instantly:
- **Blue icons** — Already in correct position, won't move
- **Orange → Red arrows** — Will move (orange = current, red = destination)
- **Green icons** — In backup but not on desktop, will be skipped

### Multi-Monitor & Resolution Questions

**Can I restore my icons after connecting an external monitor?**
Yes — the app fully supports multi-monitor setups and saves positions across all displays. It warns you if monitor count differs from the backup. Enable **Adaptive Scaling** if resolution differs.

**Does Adaptive Scaling work between very different resolutions (1080p to 4K)?**
Yes — the algorithm proportionally recalculates every icon position to fit new dimensions, so icons land in the correct area rather than piling up in corners.

**How do I manage multiple monitor configurations?**
Create separate named backups for each:
- `Laptop Only` — standalone laptop
- `Office Docked` — with external monitors
- `Home TV Setup` — with TV as secondary display
Then switch between them instantly with one click.

### Feature & Technical Questions

**Is Desktop Icon Backup Manager truly free?**
Completely free, forever, MIT licensed. No ads, no telemetry, no required accounts, no nag screens. Source code is on GitHub for inspection and contribution.

**Will antivirus software flag the .exe?**
Some antivirus tools flag programs that interact with Windows Explorer's memory, even when using only standard Win32 API calls—the same ones Windows uses internally. If flagged, add the `.exe` to your whitelist. Full source code is available on GitHub for independent verification.

**How does Desktop Icon Backup Manager compare to ReIcon and DesktopOK?**
All three tools save and restore desktop icon positions. Desktop Icon Backup Manager uniquely offers:
- **Live diff preview** — see exactly which icons will move
- **Cross-backup comparison** — diff any two saved layouts
- **Visual layout preview** — mini-map of all icon positions
- **Open-source MIT-licensed code** — fully auditable

See the [detailed comparison table](#comparison-desktop-icon-backup-manager-vs-competitors) above for complete details.

**Does the program check for updates automatically?**
Yes — by default, the program checks GitHub for new versions 10 seconds after startup. If found, a tray notification appears and a log entry is added. You can manually check anytime via **Help → Check for Updates**. Clicking "Download Update" opens the releases page. Disable via **Settings → Check for Updates on Startup**.

**Can I automate desktop icon backups with Windows Task Scheduler?**
Yes — use `desktop-icon-backup-manager.exe --backup --silent`. The process runs in the background, saves your layout, and exits immediately. Set as a login trigger in Task Scheduler for fully automatic, zero-effort backups. See the [Command-Line Automation section](#command-line-automation-advanced) for detailed instructions.

**Where are backup files stored? Can I move them?**
In the `icon_backups` subfolder next to the `.exe`. Files are plain JSON—you can copy them to another machine or store in a cloud-synced folder. Filenames include resolution and timestamp for easy identification.

**Does it work on older Windows versions?**
Yes — Desktop Icon Backup Manager is fully compatible with Windows 7, 8, 10, and 11 (including 25H2), both 32-bit and 64-bit.

---

## Troubleshooting Guide

### Desktop Icons Not Visible or Inaccessible

**Error Message:** "Unable to find desktop ListView control"

**Cause:** Desktop icons are hidden or the ListView control is inaccessible.

**Solutions:**
1. Right-click desktop → **View** → enable **Show desktop icons**
2. Restart Windows Explorer:
   - Press `Ctrl+Shift+Esc` to open Task Manager
   - Right-click **Windows Explorer** → **Restart**
3. Check for third-party desktop replacements (e.g., Stardock Fences) that might be interfering
4. Try running Desktop Icon Backup Manager as Administrator

### Icons Restore to Wrong Positions or Pile Up

**Cause:** Resolution or monitor configuration differs from when backup was saved.

**Solutions:**
1. **Enable Adaptive Scaling:**
   - Open **Settings** (Ctrl+,)
   - Check **Enable Adaptive Scaling on Restore**
   - This proportionally recalculates positions for new resolution
2. **Confirm monitor configuration:**
   - Verify the same monitors are connected
   - Check they're in the same physical arrangement as when backup was created
3. **Create configuration-specific backups:**
   - Save separate backups for each setup: `Laptop Only`, `Office Dock`, `Home TV`
   - Switch between them based on your current configuration

### Program Flagged by Antivirus

**Cause:** The app uses standard Win32 API calls to read/write icon positions—the same method Windows Explorer uses. Some antivirus heuristics flag this activity.

**Solution:**
1. Add the `.exe` to your antivirus whitelist/exclusions
2. Visit the GitHub repository for full source code inspection
3. Build from source if you prefer to verify the code yourself

### Settings Not Saved After Restart

**Cause:** Application was force-closed instead of properly exiting.

**Solutions:**
1. Always close via **File → Exit** or press `Ctrl+Q`
2. Avoid force-killing via Task Manager—this skips the settings save routine
3. Verify `settings.ini` is writable:
   - The folder must not be read-only
   - The folder must not be inside `Program Files` (requires admin to write)
   - Try moving to `C:\Tools\` or your user folder

### Application Won't Start

**Causes & Solutions:**
1. **Another instance is running:**
   - Check system tray for existing icon
   - Close existing instance before launching again
2. **Corrupt settings file:**
   - Delete `settings.ini` to reset to defaults
   - Application will recreate it on next launch
3. **Corrupt backup causes startup crash:**
   - Manually edit `settings.ini`
   - Set `auto_restore_on_startup=false`
   - Restart application
   - Fix or delete the corrupt backup
   - Re-enable auto-restore if desired

### Multi-Monitor Layout Incorrect After Restore

**Cause:** Different number of monitors or arrangement than when backup was saved.

**Solutions:**
1. **Enable Adaptive Scaling:**
   - This automatically adjusts positions for different configurations
2. **Maintain separate backups per setup:**
   - Create named backups for each configuration
   - Example: `1Monitor`, `2Monitors_DualDock`, `3Monitors_Home`
3. **Check warning dialogs:**
   - App shows warnings if monitor count differs
   - Review the diff preview before confirming restore

---

## Acknowledgments & Credits

Desktop Icon Backup Manager is built on the shoulders of excellent open-source projects:

- **[PyQt6](https://www.riverbankcomputing.com/software/pyqt/)** — Modern cross-platform GUI framework
- **[pywin32](https://github.com/mhammond/pywin32)** — Windows API bindings for Python

---

## Screenshots Gallery

### Main Window — Save & Restore Desktop Icons

<p align="center">
  <img src="images/DIBM_1.png" alt="Desktop Icon Backup Manager main window - save and restore desktop icon positions on Windows 10 and 11" width="80%">
  <br><br>
  <em>Main window interface — quickly save or restore your desktop icon layout with one click</em>
  <br><br><br>
</p>

### Backup Manager — Browse, Search & Preview Layouts

<p align="center">
  <img src="images/DIBM_2.png" alt="Backup Manager interface - browse, search, preview live diff, and restore saved desktop icon layouts" width="80%">
  <br><br>
  <em>Backup Manager — browse your entire backup history, search by tag, and preview changes with live diff visualization</em>
  <br><br><br>
</p>

### Splash Screen on Launch

<p align="center">
  <img src="images/DIBM_3.png" alt="Desktop Icon Backup Manager splash screen displayed on application launch" width="50%">
  <br><br>
  <em>Clean splash screen appears on application launch</em>
  <br><br><br>
</p>

### Dark Mode with Multi-Language Support

<p align="center">
  <img src="images/DIBM_4.png" alt="Dark mode - Desktop Icon Backup Manager with Italian language and multi-monitor support" width="80%">
  <br><br>
  <em>Dark mode with full multi-language support (shown in Italian) — supports 26 languages</em>
  <br><br><br>
</p>

### Live Diff Preview — The Unique Feature

<p align="center">
  <img src="images/DIBM_5.png" alt="Live diff preview - unique feature showing exactly which desktop icons will move before restoring" width="80%">
  <br><br>
  <em>Live diff preview (unique feature) — see exactly which icons will move (orange→red), stay (blue), or be skipped (green) before restoring</em>
  <br><br><br>
</p>

### Restore Confirmation Dialog

<p align="center">
  <img src="images/DIBM_6.png" alt="Confirmation dialog before restoring a desktop icon backup" width="50%">
  <br><br>
  <em>Confirmation dialog — always confirms before applying changes to prevent accidental icon movement</em>
  <br><br><br>
</p>

---

## Related Resources & Further Reading

- **[Windows Desktop Icon Troubleshooting Guide](https://support.microsoft.com/en-us/windows)** — Official Microsoft support documentation
- **[How to Fix Desktop Icons Rearranging](https://www.howtogeek.com)** — Comprehensive troubleshooting guides
- **[PyQt6 Documentation](https://www.riverbankcomputing.com/software/pyqt/intro)** — GUI framework documentation
- **[Windows API Reference](https://learn.microsoft.com/en-us/windows/win32/)** — Complete Windows API documentation

---

## License & Legal Information

Desktop Icon Backup Manager is released under the **MIT License**, one of the most permissive open-source licenses available.

**You are free to:**
- Use the software for any purpose, commercial or personal
- Modify the source code
- Distribute the software
- Use the software privately

**You must:**
- Include a copy of the license
- Include a copyright notice

**See the full license:** [MIT License](https://opensource.org/licenses/MIT)




