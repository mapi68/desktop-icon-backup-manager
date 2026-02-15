# Desktop Icon Backup Manager

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

## 🌟 Features

### Core Functionality
- **💾 Quick Backup**: Save your desktop icon layout with a single click
- **↺ Restore Options**: Restore from the latest backup or choose from a list of saved configurations
- **🏷️ Custom Tags**: Add descriptive tags to your backups for easy identification
- **📊 Resolution Tracking**: Automatically records screen resolution with each backup

### Advanced Features
- **🖼️ Visual Layout Preview**: See a mini-map of your icon arrangement before restoring
- **🔄 Adaptive Scaling**: Automatically adjusts icon positions when restoring to different screen resolutions
- **🖥️ Multi-Monitor Support**: Detects and handles multiple monitor configurations
- **🗑️ Smart Cleanup**: Automatic deletion of old backups (configurable limits: 5, 10, 25, 50, or unlimited)
- **⚡ System Tray Integration**: Run minimized in the background with quick access to save/restore

### Automation
- **Auto-Save on Exit**: Automatically backup your layout when closing the application
- **Auto-Restore on Startup**: Automatically restore your layout when the application starts
- **Background Operations**: Non-blocking operations with progress indicators

### User Experience
- **Dark Theme Support**: Adapts to your Windows theme preferences
- **Keyboard Shortcuts**: `Ctrl+S` for quick save, `Ctrl+Q` to exit
- **Detailed Activity Log**: Track all operations with timestamped entries
- **Confirmation Dialogs**: Prevent accidental overwrites or deletions

## 📋 Requirements

- Windows 7 or higher (fully compatible with Windows 11)
- Python 3.8+ (for running from source)
- Desktop icons must be visible (not hidden)

## 🚀 Installation

### Option 1: Download Pre-compiled Executable (Recommended)
1. Download the latest `desktop-icon-backup-manager.exe` from the [Releases](../../releases) page
2. Extract in a folder
3. Run the executable - no installation required!

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
   python desktop-icon-backup-manager.py
   ```

## 📖 Usage Guide

### Basic Operations

#### Saving Your Layout
1. Click **"💾 SAVE QUICK BACKUP"** for an instant backup with timestamp

#### Restoring Your Layout
1. Click **"↺ RESTORE LATEST"** to restore from the most recent backup
2. Or click **"↺ BACKUP MANAGER"** to choose from all available backups

### Advanced Features

#### System Tray Usage
- **Minimize to Tray**: Close the window (when "Minimize to Tray" is enabled in Settings)
- **Quick Actions**: Right-click the tray icon for quick save/restore options
- **Double-Click**: Restore the main window

#### Settings Menu

**Auto-Save/Auto-Restore**
- ✅ **Auto-Save on Exit**: Automatically creates a backup when closing the app
- ✅ **Auto-Restore on Startup**: Automatically restores the latest backup on launch

**Adaptive Scaling**
- ✅ **Enable Adaptive Scaling on Restore**: Automatically adjusts icon positions when restoring to a different screen resolution
  - Example: Backup saved at 1920x1080 → Restored at 2560x1440

**Backup Management**
- **Automatic Cleanup Limit**: Choose how many backups to keep (5, 10, 25, 50, or unlimited)
- Oldest backups are automatically deleted when the limit is reached

**Startup Behavior**
- ✅ **Start Minimized to Tray**: Launch the app in the system tray

**Window Behavior**
- ✅ **Minimize to Tray on Close**: Hide to tray instead of closing when clicking 'X'

### Backup File Format

Backups are stored in the `icon_backups` folder as JSON files with the format:
```
[Resolution]_[Timestamp].json
Example: 1920x1080_20240315_143022.json
```

Each backup contains:
- Icon positions (name and coordinates)
- Display metadata (resolution, monitor count)
- Custom description/tag
- Timestamp

## ⚙️ Configuration

Settings are automatically saved to `settings.ini` in the application directory:

```ini
[General]
auto_save_on_exit=true
auto_restore_on_startup=false
adaptive_scaling_enabled=true
cleanup_limit=10
start_minimized=false
close_to_tray=true
```

## 🔧 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Quick Save |
| `Ctrl+M` | Open Backup Manager |
| `Ctrl+,` | Open Settings menu |
| `Ctrl+Q` | Exit Application |
| `F1`     | Open Online User Manual |

## 🐛 Troubleshooting

### Icons not restoring correctly?
- Ensure desktop icons are visible (not hidden)
- Check that the Activity Log for any error messages
- Try disabling "Auto-arrange icons" in Windows desktop settings

### Application won't start?
- Make sure no other instance is running
- Check that you have the required permissions
- Verify that desktop icons are enabled in Windows

### Multi-monitor issues?
- Enable "Adaptive Scaling" in Settings for automatic position adjustment
- Note: Backup saves the configuration from the time it was created
- Restoring with different monitor setup may require manual adjustments

## 🙏 Acknowledgments

- Built with PyQt6 for the modern GUI
- Uses Win32 API for desktop icon manipulation
- Inspired by the need to preserve desktop layouts across resolution changes

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
  <img src="images/DIBM_3.png" width="50%" title="Confirmation dialog before restoring a backup">
  <br><br>
  <em>Confirmation dialog before restoring a backup</em>
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
