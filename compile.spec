# -*- mode: python ; coding: utf-8 -*-
import os

# --- 1. VERSIONING ---
try:
    with open("version.txt", "r", encoding="utf-8") as f:
        VERSIONE = f.read().strip()
except Exception:
    VERSIONE = "0.0.0"

def get_version_tuple(v_str):
    try:
        parts = [int(x) for x in v_str.split('.')]
        while len(parts) < 4:
            parts.append(0)
        return tuple(parts[:4])
    except Exception:
        return (0, 0, 0, 0)

v_tuple = get_version_tuple(VERSIONE)

# --- 2. VERSION INFO FILE GENERATION ---
FILE_DESCRIPTION = (
    'A utility that allows to manage the positions of Windows desktop icons'
)

version_info_content = (
    "# UTF-8\n"
    "VSVersionInfo(\n"
    "  ffi=FixedFileInfo(\n"
    f"    filevers={v_tuple},\n"
    f"    prodvers={v_tuple},\n"
    "    mask=0x3f,\n"
    "    flags=0x0,\n"
    "    OS=0x4,\n"
    "    fileType=0x1,\n"
    "    subtype=0x0,\n"
    "    date=(0, 0)\n"
    "    ),\n"
    "  kids=[\n"
    "    StringFileInfo(\n"
    "      [\n"
    "      StringTable(\n"
    "        '040904b0',\n"
    "        [StringStruct('CompanyName', 'mapi68'),\n"
    f"        StringStruct('FileDescription', '{FILE_DESCRIPTION}'),\n"
    f"        StringStruct('FileVersion', '{VERSIONE}'),\n"
    "        StringStruct('InternalName', 'desktop-icon-backup-manager'),\n"
    f"        StringStruct('LegalCopyright', '\xa9 2026 mapi68'),\n"
    f"        StringStruct('OriginalFilename', 'desktop-icon-backup-manager_{VERSIONE}.exe'),\n"
    "        StringStruct('ProductName', 'Desktop Icon Backup Manager'),\n"
    f"        StringStruct('ProductVersion', '{VERSIONE}')])\n"
    "      ]),\n"
    "    VarFileInfo([VarStruct('Translation', [0, 1200])])\n"
    "  ]\n"
    ")\n"
)

VERSION_INFO_PATH = 'version_info.txt'
with open(VERSION_INFO_PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(version_info_content)

# --- 3. QT BASE TRANSLATIONS ---
# Resolve Qt's own translations folder at build time so PyInstaller
# can bundle qtbase_*.qm files — needed to localise standard buttons
# (Yes / No / OK / Cancel / Close …) in each language.
import glob as _glob
from PyQt6.QtCore import QLibraryInfo as _QLib
from PyQt6.QtWidgets import QApplication as _QApp
_qt_app = _QApp.instance() or _QApp([])
_qt_tr_path = _QLib.path(_QLib.LibraryPath.TranslationsPath)
_qtbase_qms = _glob.glob(os.path.join(_qt_tr_path, 'qtbase_*.qm'))

# --- 4. ANALYSIS ---
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('icon.png', '.'),
        ('i18n/*.qm', 'i18n'),
        ('version.txt', '.'),
        *[(_qm, 'qt_translations') for _qm in _qtbase_qms],
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'desktop-icon-backup-manager_{VERSIONE}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    version=VERSION_INFO_PATH,
)