# Desktop Icon Backup Manager

[![☕ Liked this tool? Buy me a coffee! — ko-fi.com/mapi68](https://img.shields.io/badge/-%E2%98%95%20Liked%20this%20tool%3F%20%20Buy%20me%20a%20coffee!%20%E2%80%94%20ko--fi.com%2Fmapi68-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white&labelColor=1a1a2e)](https://ko-fi.com/mapi68)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Windows](https://img.shields.io/badge/Platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![GitHub release](https://img.shields.io/github/v/release/mapi68/desktop-icon-backup-manager?style=for-the-badge&logo=github&color=2ea44f)](https://github.com/mapi68/desktop-icon-backup-manager/releases)
[![GitHub All Releases](https://img.shields.io/github/downloads/mapi68/desktop-icon-backup-manager/total?style=for-the-badge&logo=github-actions&color=6f42c1)](https://github.com/mapi68/desktop-icon-backup-manager/releases)
[![License](https://img.shields.io/badge/License-MIT-41AD49?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

---

## 📖 Documentation

[![User Manual](https://img.shields.io/badge/Manual-PDF-EC1C24?style=for-the-badge&logo=adobe-acrobat-reader&logoColor=white)](https://mapi68.github.io/desktop-icon-backup-manager/manual.pdf)

> [!TIP]
> You can always access the latest updated documentation at the following link: [User Manual (PDF)](https://mapi68.github.io/desktop-icon-backup-manager/manual.pdf)

---

## 🛠️ Development Status

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg?style=for-the-badge&logo=github)](https://github.com/mapi68/desktop-icon-backup-manager/graphs/commit-activity)
[![GitHub last commit](https://img.shields.io/github/last-commit/mapi68/desktop-icon-backup-manager?style=for-the-badge&logo=git&color=f05032)](https://github.com/mapi68/desktop-icon-backup-manager/commits/master)
[![GitHub release date](https://img.shields.io/github/release-date/mapi68/desktop-icon-backup-manager?style=for-the-badge&logo=clock&color=007ec6)](https://github.com/mapi68/desktop-icon-backup-manager/releases)

---

## ✨ Features

### Core Functionality
- **💾 Quick Backup**: Save your desktop icon layout with a single click, with an optional descriptive tag
- **↺ Restore Options**: Restore from the latest backup or choose from a list of saved configurations
- **🏷️ Custom Tags**: Add descriptive tags to your backups for easy identification
- **📊 Resolution Tracking**: Automatically records screen resolution and monitor metadata with each backup

### Advanced Features
- **🔍 Live Diff Preview**: Before restoring, see a color-coded overlay showing exactly which icons will move (orange→red with arrow), which are already in place (blue), and which are missing from the desktop (green)
- **🖼️ Visual Layout Preview**: See a mini-map of your icon arrangement before restoring, with interactive tooltips showing icon names
- **🔄 Adaptive Scaling**: Automatically adjusts icon positions when restoring to a different screen resolution
- **🖥️ Multi-Monitor Support**: Detects and handles multiple monitor configurations, with warnings when the setup differs from the saved backup
- **⚖️ Flexible Comparison**: Compare **any two backups** against each other (not just vs. latest) to see added, removed, and moved icons — via context menu or the dedicated "Compare Two Selected…" button
- **🗑️ Smart Cleanup**: Automatic deletion of old backups when a configured limit is reached (5, 10, 25, 50, or unlimited)
- **⚡ System Tray Integration**: Run minimized in the background with quick access to save/restore from the tray icon

### Automation & CLI
- **Auto-Save on Exit**: Automatically backup your layout when closing the application
- **Auto-Restore on Startup**: Automatically restore the latest backup when the application starts
- **Command Line Interface**: Run headless backup and restore operations for scripting and scheduled tasks
- **Background Operations**: All operations run in a separate thread with real-time progress indicators

### User Experience
- **📋 Sortable Backup Table**: Click any column header (Tag, Resolution, Icons, Timestamp) to sort the backup list
- **↔️ Resizable Backup Manager**: The window adapts to any screen size or DPI setting
- **🌍 Multi-language**: Auto-detected from system locale or manually selected
- **⌨️ Keyboard Shortcuts**: Full keyboard navigation — see [shortcuts table](#%EF%B8%8F-keyboard-shortcuts) below
- **📋 Detailed Activity Log**: Track all operations with timestamped entries; copy log with `Ctrl+A` / `Ctrl+C`
- **✅ Confirmation Dialogs**: Prevent accidental overwrites or deletions

---

## 📋 Requirements

- Windows 7 or higher (fully compatible with Windows 11)
- Python 3.8+ (only if running from source)
- Desktop icons must be visible (`Right-click desktop → View → Show desktop icons`)
- No administrator rights required

---

## 🚀 Installation

### Option 1: Download Pre-compiled Executable (Recommended)
1. Download the latest `desktop-icon-backup-manager.exe` from the [Releases](../../releases) page
2. Place it in a dedicated folder
3. Run the executable — no installation required!

### Option 2: Run from Source
1. Clone this repository:
   ```bash
   git clone https://github.com/mapi68/desktop-icon-backup-manager.git
   cd desktop-icon-backup-manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

---

## 📖 Usage Guide

### Basic Operations

#### Saving Your Layout
1. *(Optional)* Type a descriptive tag in the **Save Tag** field (e.g. `Work Setup`, `Before Update`)
2. Click **💾 SAVE QUICK BACKUP** — or press `Ctrl+S` — to create a timestamped backup

> [!NOTE]
> When using `Ctrl+S`, the backup is tagged *"Quick Backup (Shortcut)"* regardless of what is typed in the tag field. To apply a custom tag, use the button click.

#### Restoring Your Layout
1. Click **↺ RESTORE LATEST** to restore from the most recent backup (a confirmation dialog is shown first)
2. Or click **↺ BACKUP MANAGER** (`Ctrl+M`) to browse, preview, and restore any saved backup

---

### Advanced Features

#### Live Diff Preview

When you select a backup in the Backup Manager, the preview panel fetches the **current live positions** from the desktop and renders a color-coded diff directly on a desktop-like canvas with a subtle grid:

| Visual | Meaning |
|--------|---------|
| 🔵 **Blue dot** (with soft halo) | Already in place, will not move |
| 🟠 **Orange dot** ──▶ 🔴 **Red dot** | Will move: orange = current position, red = target from backup |
| 🟢 **Green dot** | In backup, not on desktop (will be skipped on restore) |

A compact legend panel displayed **outside the canvas** (to the right of the backup info box) shows the colour coding used in the diff preview. Hover over any dot to see the icon name and status.

#### Command Line Interface (CLI)

The application supports headless operation for scripting and scheduled tasks. When `--backup`, `--restore`, or `--silent` is passed, no GUI is shown and the process exits immediately after the operation.

```bash
# Silent backup (uses settings.ini for cleanup limit)
desktop-icon-backup-manager.exe --backup --silent

# Restore the most recent backup silently
desktop-icon-backup-manager.exe --restore latest --silent

# Restore a specific backup file
desktop-icon-backup-manager.exe --restore "1920x1080_20241211_143015.json" --silent
```

**Exit codes:** `0` = success, `1` = error.

**Automation with Windows Task Scheduler:**
1. Open Task Scheduler → Create Basic Task
2. Set trigger (e.g. Daily, or On logon)
3. Action: Start a program → path to `desktop-icon-backup-manager.exe`
4. Add arguments: `--backup --silent`

#### System Tray Usage
- **Right-click** the tray icon for quick Save / Restore Latest / Show Window / Exit
- **Double-click** to show or hide the main window
- Notifications appear for completed operations even when the window is hidden

#### Backup Manager
- **Search/filter** backups by tag, resolution, or date in real time
- **Sortable table**: click any column header (Tag, Resolution, Icons, Timestamp) to sort
- **Live diff preview** shows which icons will move before you confirm a restore (see above)
- **Visual preview** shows a dot-map of icon positions; hover over dots to see icon names
- **Compare any two backups** via right-click → *Compare with Latest*, or select one backup and click **"Compare Two Selected…"** to pick any second backup
- **Right-click** a backup for Restore, Compare, or Delete options

---

### Settings

| Setting | Description |
|---------|-------------|
| **Start Minimized to Tray** | Launch the app hidden in the system tray |
| **Auto-Save on Exit** | Create a backup automatically when closing the app |
| **Auto-Restore on Startup** | Restore the latest backup automatically on launch |
| **Enable Adaptive Scaling on Restore** | Scale icon positions proportionally when restoring to a different resolution |
| **Minimize to Tray on Close** | Hide to tray instead of quitting when clicking the X button |
| **Automatic Backup Cleanup Limit** | Keep only the N most recent backups (5 / 10 / 25 / 50 / unlimited) |

> [!WARNING]
> Combining **Auto-Save on Exit** with **Auto-Restore on Startup** creates an automatic save/restore cycle. If icons are in wrong positions when you exit, those wrong positions will be restored on next startup. Use the Backup Manager to restore a known-good layout if needed.

---

## ⚙️ Configuration

Settings are stored in `settings.ini` in the application directory and are created automatically on first run:

```ini
[General]
start_minimized=false
auto_save_on_exit=false
auto_restore_on_startup=false
adaptive_scaling_enabled=false
close_to_tray=false
cleanup_limit=0
geometry=@Rect(100 100 800 650)
```

> [!TIP]
> You can edit `settings.ini` directly with any text editor. Changes take effect on the next program launch. Invalid values are automatically reset to defaults.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Quick Save current layout |
| `Ctrl+M` | Open Backup Manager |
| `Ctrl+,` | Open Settings menu |
| `Ctrl+Q` | Exit Application |
| `F1`     | Open Online User Manual |

---

## 📁 Backup File Format

Backups are stored as JSON files in the `icon_backups` subfolder, created automatically next to the executable.

**File naming:**
```
{width}x{height}_{YYYYMMDD}_{HHMMSS}.json
Example: 1920x1080_20241211_143015.json
```

**File structure:**
```json
{
    "timestamp": "2024-12-11T14:30:15.123456",
    "icon_count": 12,
    "description": "Work Setup Final",
    "display_metadata": {
        "monitor_count": 2,
        "primary_resolution": "1920x1080",
        "screens": [...]
    },
    "icons": {
        "This PC": [100, 200],
        "Recycle Bin": [100, 350]
    }
}
```

Each backup file is typically 2–10 KB. With 50 backups, total storage is under 500 KB.

---

## 🐛 Troubleshooting

### "Unable to find desktop ListView control"
Desktop icons are hidden or inaccessible.
- Right-click the desktop → **View** → enable **Show desktop icons**
- Restart Windows Explorer via Task Manager if the error persists
- Check that no third-party desktop replacement software is active

### Icons restored to wrong positions
- Enable **Adaptive Scaling on Restore** in the Settings menu
- Make sure the same monitors are connected in the same arrangement as when the backup was created
- Create separate backups for each monitor configuration (e.g. `Laptop Only`, `Docked - 2 Monitors`)

### Program flagged by antivirus
The program accesses Windows Explorer's memory to read and write icon positions (standard Win32 API). Some antivirus tools may flag this behavior. Add the executable to your antivirus whitelist.

### Settings not saved after restart
- Make sure the application is closed via **File → Exit** or `Ctrl+Q`, not via Task Manager
- Check that `settings.ini` is writable (the folder must not be read-only or protected)

### Application won't start
- Only one instance can run at a time — check if it is already running in the system tray
- If the app crashes immediately, delete `settings.ini` to reset all settings to defaults
- If **Auto-Restore on Startup** is causing a crash, set `auto_restore_on_startup=false` in `settings.ini` manually

### Multi-monitor issues
- Enable **Adaptive Scaling** for automatic position adjustment between similar resolutions
- For very different configurations, create and restore dedicated backups per setup
- A warning dialog will appear if the number of monitors differs from the saved backup

---

## 🙏 Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI
- Uses [pywin32](https://github.com/mhammond/pywin32) for Win32 API access to desktop icon positions

---

## ☕ Support

If this tool saved you even 5 minutes of frustration, consider buying me a coffee — it helps keep the project alive and growing!

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/mapi68)

---

## 📸 Screenshots

<p align="center">
  <img src="images/DIBM_1.png" width="80%" title="Main interface showing the activity log and three main action buttons">
  <br><br>
  <em>Main interface showing the activity log and three main action buttons</em>
  <br><br><br>
</p>

<p align="center">
  <img src="images/DIBM_2.png" width="80%" title="Backup Manager window with list of saved backups and layout preview">
  <br><br>
  <em>Backup Manager window with list of saved backups and layout preview</em>
  <br><br><br>
</p>

<p align="center">
  <img src="images/DIBM_3.png" width="50%" title="Loading Desktop Backup Manager...">
  <br><br>
  <em>Loading Desktop Backup Manager...</em>
  <br><br><br>
</p>

<p align="center">
  <img src="images/DIBM_4.png" width="80%" title="Desktop Icon Backup Manager featuring dark mode and Italian support">
  <br><br>
  <em>Desktop Icon Backup Manager featuring dark mode and Italian support</em>
  <br><br><br>
</p>

<p align="center">
  <img src="images/DIBM_5.png" width="80%" title="Detailed view of the comparison interface">
  <br><br>
  <em>Detailed view of the comparison interface</em>
  <br><br><br>
</p>

<p align="center">
  <img src="images/DIBM_6.png" width="50%" title="Confirmation dialog before restoring a backup">
  <br><br>
  <em>Confirmation dialog before restoring a backup</em>
  <br><br><br>
</p>
