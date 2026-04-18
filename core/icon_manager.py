"""Desktop Icon Manager - Core functionality for managing icon positions"""

import json
import logging
import os
import random
import struct
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional, Callable, List

import win32api
import win32con
import win32gui
import win32process

from PyQt6.QtCore import QCoreApplication

from core.config import Config, Win32Constants, LVITEMW
from utils.helpers import (
    get_display_metadata,
    parse_backup_filename,
    parse_resolution_string,
)

logger = logging.getLogger("dibm")


def _pack_lparam(x: int, y: int) -> int:
    """
    Pack (x, y) pixel coordinates into a Win32 LPARAM for LVM_SETITEMPOSITION.

    Handles negative coordinates correctly (e.g. multi-monitor setups where
    monitors are positioned to the left / above the primary).  Both values are
    masked to 16-bit signed two's complement so the shell interprets them
    correctly regardless of sign.
    """
    # Bug 5 fix: mask *both* components to 16-bit, not just x
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


class DesktopIconManager:
    """Manages saving and restoring desktop icon positions"""

    def __init__(self):
        self.hwnd_listview = self._get_desktop_listview_hwnd()
        self._ensure_backup_directory()

    def _ensure_backup_directory(self) -> None:
        """Create backup directory if it doesn't exist"""
        Path(Config.BACKUP_DIR).mkdir(exist_ok=True)

    def _get_desktop_listview_hwnd(self) -> int:
        """Get handle to desktop ListView control"""
        hwnd_progman = win32gui.FindWindow("Progman", None)
        hwnd_shell = win32gui.FindWindowEx(hwnd_progman, 0, "SHELLDLL_DefView", None)
        hwnd_listview = win32gui.FindWindowEx(hwnd_shell, 0, "SysListView32", None)

        if not hwnd_listview:

            def enum_windows_callback(hwnd, lParam):
                hwnd_shell = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                if hwnd_shell:
                    hwnd_listview_found = win32gui.FindWindowEx(
                        hwnd_shell, 0, "SysListView32", None
                    )
                    if hwnd_listview_found:
                        lParam.append(hwnd_listview_found)
                return True

            hwnds = []
            win32gui.EnumWindows(enum_windows_callback, hwnds)
            if hwnds:
                hwnd_listview = hwnds[0]

        if not hwnd_listview:
            raise RuntimeError(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "Unable to find desktop ListView control. Make sure desktop icons are visible.",
                )
            )
        return hwnd_listview

    def _list_backup_files(self) -> List[str]:
        """List all backup files sorted by date (newest first)"""
        if not os.path.exists(Config.BACKUP_DIR):
            return []
        backup_files = [f for f in os.listdir(Config.BACKUP_DIR) if f.endswith(".json")]
        backup_files.sort(key=lambda f: parse_backup_filename(f)[2], reverse=True)
        return backup_files

    def get_latest_backup_filename(self) -> Optional[str]:
        """Get the most recent backup filename"""
        backup_files = self._list_backup_files()
        return backup_files[0] if backup_files else None

    def get_all_backup_filenames(self) -> List[str]:
        """Get all backup filenames"""
        return self._list_backup_files()

    def delete_backup(self, filename: str) -> bool:
        """Delete a specific backup file"""
        filepath = os.path.join(Config.BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            # Already gone — treat as success
            return True
        try:
            os.remove(filepath)
            return True
        except OSError as e:
            logger.error("Error deleting file %s: %s", filepath, e)
            return False

    def delete_all_backups(self, log_callback: Callable[[str], None]) -> bool:
        """Delete all backup files"""
        backup_files = self._list_backup_files()
        if not backup_files:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "No backup files found to delete."
                )
            )
            return True

        deleted_count = 0
        failed_count = 0
        for filename in backup_files:
            if self.delete_backup(filename):
                deleted_count += 1
            else:
                failed_count += 1

        if deleted_count > 0:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "✓ Successfully deleted %n backup file(s).",
                    None,
                    deleted_count,
                )
            )
        if failed_count > 0:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "✗ Failed to delete %n backup file(s).",
                    None,
                    failed_count,
                )
            )
            return False
        return True

    def cleanup_old_backups(
        self, max_count: int, log_callback: Callable[[str], None]
    ) -> None:
        """Clean up old backups beyond max_count"""
        if max_count <= 0:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "Automatic cleanup skipped: max_count is disabled (0).",
                )
            )
            return

        backup_files = self._list_backup_files()
        current_count = len(backup_files)

        if current_count <= max_count:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "Cleanup skipped: Current count (%n) is within the limit (%1).",
                    None,
                    current_count,
                ).replace("%1", str(max_count))
            )
            return

        files_to_delete = backup_files[max_count:]
        deleted_count = 0

        log_callback(
            QCoreApplication.translate(
                "DesktopIconManager",
                "Cleanup needed: Current count (%1) exceeds limit (%2). Deleting %n oldest file(s).",
                None,
                len(files_to_delete),
            )
            .replace("%1", str(current_count))
            .replace("%2", str(max_count))
        )

        for filename in files_to_delete:
            if self.delete_backup(filename):
                deleted_count += 1
                log_callback(
                    QCoreApplication.translate(
                        "DesktopIconManager", "  Deleted oldest backup: %1"
                    ).replace("%1", str(filename))
                )
            else:
                log_callback(
                    QCoreApplication.translate(
                        "DesktopIconManager", "  Failed to delete: %1"
                    ).replace("%1", str(filename))
                )

        log_callback(
            QCoreApplication.translate(
                "DesktopIconManager",
                "Cleanup complete. Total deleted: %n file(s).",
                None,
                deleted_count,
            )
        )

    def _get_latest_backup_path(self) -> Optional[str]:
        """Get path to latest backup file"""
        latest_file = self.get_latest_backup_filename()
        if latest_file:
            return os.path.join(Config.BACKUP_DIR, latest_file)
        return None

    def get_current_icon_positions(self) -> Dict[str, Tuple[int, int]]:
        """
        Read the current live icon positions from the desktop ListView.
        Returns a dict mapping icon name -> (x, y).
        """
        icons: Dict[str, Tuple[int, int]] = {}
        pid = win32process.GetWindowThreadProcessId(self.hwnd_listview)[1]
        process_handle = None
        remote_memory = None
        try:
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, pid
            )
            remote_memory = win32process.VirtualAllocEx(
                process_handle,
                0,
                Config.REMOTE_BUFFER_SIZE,
                Win32Constants.MEM_COMMIT,
                Win32Constants.PAGE_READWRITE,
            )
            count = win32gui.SendMessage(
                self.hwnd_listview, Win32Constants.LVM_GETITEMCOUNT, 0, 0
            )
            text_buffer_remote = remote_memory + Config.TEXT_BUFFER_OFFSET
            for i in range(count):
                win32gui.SendMessage(
                    self.hwnd_listview,
                    Win32Constants.LVM_GETITEMPOSITION,
                    i,
                    remote_memory,
                )
                point_data = win32process.ReadProcessMemory(
                    process_handle, remote_memory, 8
                )
                x, y = struct.unpack("ii", point_data)

                lvitem = LVITEMW()
                lvitem.mask = 0x0001
                lvitem.iItem = i
                lvitem.iSubItem = 0
                lvitem.pszText = text_buffer_remote
                lvitem.cchTextMax = 512

                win32process.WriteProcessMemory(
                    process_handle, remote_memory, bytes(lvitem)
                )
                win32gui.SendMessage(
                    self.hwnd_listview,
                    Win32Constants.LVM_GETITEMTEXTW,
                    i,
                    remote_memory,
                )
                text_raw = win32process.ReadProcessMemory(
                    process_handle, text_buffer_remote, 512 * 2
                )
                icon_name = text_raw.decode("utf-16-le").split("\0", 1)[0]
                if icon_name:
                    icons[icon_name] = (x, y)
        except Exception as e:
            logger.error("Error reading current icon positions: %s", e)
        finally:
            if remote_memory and remote_memory != 0 and process_handle:
                win32process.VirtualFreeEx(
                    process_handle, remote_memory, 0, Win32Constants.MEM_RELEASE
                )
            if process_handle:
                win32api.CloseHandle(process_handle)
        return icons

    def save(
        self,
        log_callback: Callable[[str], None],
        progress_callback: Optional[Callable[[int], None]] = None,
        description: Optional[str] = None,
        max_backup_count: int = 0,
    ) -> bool:
        """Save current icon positions"""
        display_metadata = get_display_metadata()
        resolution = display_metadata.get("primary_resolution", "UnknownResolution")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{resolution}_{timestamp}.json"
        filepath = os.path.join(Config.BACKUP_DIR, filename)

        pid = win32process.GetWindowThreadProcessId(self.hwnd_listview)[1]
        process_handle = None
        remote_memory = None

        try:
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, pid
            )
            remote_memory = win32process.VirtualAllocEx(
                process_handle,
                0,
                Config.REMOTE_BUFFER_SIZE,
                Win32Constants.MEM_COMMIT,
                Win32Constants.PAGE_READWRITE,
            )

            count = win32gui.SendMessage(
                self.hwnd_listview, Win32Constants.LVM_GETITEMCOUNT, 0, 0
            )
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "Monitor Resolution: %1"
                ).replace("%1", str(resolution))
            )
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "Found %n icon(s). Starting scan...",
                    None,
                    count,
                )
            )

            icons: Dict[str, Tuple[int, int]] = {}
            text_buffer_remote = remote_memory + Config.TEXT_BUFFER_OFFSET

            for i in range(count):
                if progress_callback:
                    progress_callback(int((i / count) * 100))

                win32gui.SendMessage(
                    self.hwnd_listview,
                    Win32Constants.LVM_GETITEMPOSITION,
                    i,
                    remote_memory,
                )
                point_data = win32process.ReadProcessMemory(
                    process_handle, remote_memory, 8
                )
                x, y = struct.unpack("ii", point_data)

                lvitem = LVITEMW()
                lvitem.mask = 0x0001
                lvitem.iItem = i
                lvitem.iSubItem = 0
                lvitem.pszText = text_buffer_remote
                lvitem.cchTextMax = 512

                win32process.WriteProcessMemory(
                    process_handle, remote_memory, bytes(lvitem)
                )
                win32gui.SendMessage(
                    self.hwnd_listview,
                    Win32Constants.LVM_GETITEMTEXTW,
                    i,
                    remote_memory,
                )
                text_raw = win32process.ReadProcessMemory(
                    process_handle, text_buffer_remote, 512 * 2
                )
                full_text = text_raw.decode("utf-16-le")
                icon_name = full_text.split("\0", 1)[0]

                if icon_name:
                    icons[icon_name] = (x, y)

            profile_data = {
                "timestamp": datetime.now().isoformat(),
                "icon_count": len(icons),
                "description": description if description else "",
                "display_metadata": display_metadata,
                # True from the moment the app declared itself DPI-aware.
                # Old backups (missing this key) were saved with a
                # DPI-unaware process, so their "resolution" is Windows'
                # logical/scaled size while "icons" hold physical pixels.
                # Restore logic uses this flag to compensate automatically.
                "dpi_aware": True,
                "icons": icons,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=4, ensure_ascii=False)

            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "✓ Saved %n icon(s) to backup file '%1'",
                    None,
                    len(icons),
                ).replace("%1", str(filename))
            )

            if description:
                log_callback(
                    QCoreApplication.translate(
                        "DesktopIconManager", "  (Description: %1)"
                    ).replace("%1", str(description))
                )

            self.cleanup_old_backups(max_backup_count, log_callback)

            if progress_callback:
                progress_callback(100)
            return True

        except OSError as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error saving (I/O): %1"
                ).replace("%1", str(e))
            )
            return False
        except Exception as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error saving: %1"
                ).replace("%1", str(e))
            )
            return False
        finally:
            if remote_memory and remote_memory != 0 and process_handle:
                win32process.VirtualFreeEx(
                    process_handle, remote_memory, 0, Win32Constants.MEM_RELEASE
                )
            if process_handle:
                win32api.CloseHandle(process_handle)

    def restore(
        self,
        log_callback: Callable[[str], None],
        filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
        enable_scaling: bool = False,
    ) -> Tuple[bool, Optional[Dict]]:
        """Restore icon positions from backup"""
        if filename:
            filepath = os.path.join(Config.BACKUP_DIR, filename)
        else:
            filepath = self._get_latest_backup_path()

        if not filepath or not os.path.exists(filepath):
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error: Backup file not found."
                )
            )
            return False, None

        filename = Path(filepath).name
        readable_date, resolution_saved, _ = parse_backup_filename(filename)

        log_callback(
            QCoreApplication.translate(
                "DesktopIconManager", "Attempting to restore from backup: '%1'"
            ).replace("%1", str(filename))
        )
        log_callback(
            QCoreApplication.translate(
                "DesktopIconManager", "Saved Resolution (from filename): %1"
            ).replace("%1", str(resolution_saved))
        )

        saved_metadata = None
        description = "N/A"

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            if not (
                isinstance(profile_data, dict)
                and "icons" in profile_data
                and isinstance(profile_data["icons"], dict)
            ):
                log_callback(
                    QCoreApplication.translate(
                        "DesktopIconManager",
                        "✗ Error: Invalid backup structure (missing 'icons' dictionary).",
                    )
                )
                return False, None

            saved_icons = profile_data["icons"]
            saved_metadata = profile_data.get("display_metadata")
            description = profile_data.get("description", "N/A")
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "Restoring layout (saved: %1)"
                ).replace("%1", str(readable_date))
            )
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "  Description: %1"
                ).replace("%1", str(description))
            )

        except json.JSONDecodeError as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error: Invalid backup file format: %1"
                ).replace("%1", str(e))
            )
            return False, None
        except OSError as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error reading backup file (I/O): %1"
                ).replace("%1", str(e))
            )
            return False, None

        scaling_active = False
        scale_x, scale_y = 1.0, 1.0
        current_metadata = get_display_metadata()
        current_res_str = current_metadata.get(
            "primary_resolution", "UnknownResolution"
        )
        current_res = parse_resolution_string(current_res_str)
        saved_res = parse_resolution_string(resolution_saved)

        if not enable_scaling and current_res != saved_res:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "⚠ Warning: Resolution mismatch!"
                )
            )

        if enable_scaling and current_res and saved_res and current_res != saved_res:
            scale_x = current_res[0] / saved_res[0]
            scale_y = current_res[1] / saved_res[1]
            scaling_active = True
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✓ Adaptive Scaling enabled: X=%1, Y=%2"
                )
                .replace("%1", f"{scale_x:.3f}")
                .replace("%2", f"{scale_y:.3f}")
            )

        win32gui.SendMessage(self.hwnd_listview, win32con.WM_SETREDRAW, 0, 0)

        pid = win32process.GetWindowThreadProcessId(self.hwnd_listview)[1]
        process_handle = None
        remote_memory = None

        try:
            process_handle = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, pid
            )
            remote_memory = win32process.VirtualAllocEx(
                process_handle,
                0,
                Config.REMOTE_BUFFER_SIZE,
                Win32Constants.MEM_COMMIT,
                Win32Constants.PAGE_READWRITE,
            )

            count = win32gui.SendMessage(
                self.hwnd_listview, Win32Constants.LVM_GETITEMCOUNT, 0, 0
            )
            current_map: Dict[str, int] = {}

            text_buffer_remote = remote_memory + Config.TEXT_BUFFER_OFFSET
            for i in range(count):
                if progress_callback:
                    progress_callback(int((i / (count * 2)) * 100))

                lvitem = LVITEMW()
                lvitem.mask = 0x0001
                lvitem.iItem = i
                lvitem.pszText = text_buffer_remote
                lvitem.cchTextMax = 512

                win32process.WriteProcessMemory(
                    process_handle, remote_memory, bytes(lvitem)
                )
                win32gui.SendMessage(
                    self.hwnd_listview,
                    Win32Constants.LVM_GETITEMTEXTW,
                    i,
                    remote_memory,
                )
                text_raw = win32process.ReadProcessMemory(
                    process_handle, text_buffer_remote, 512 * 2
                )
                icon_name = text_raw.decode("utf-16-le").split("\0", 1)[0]
                if icon_name:
                    current_map[icon_name] = i

            moved_count = 0
            skipped_count = 0
            total_saved = len(saved_icons)

            for idx, (name, pos) in enumerate(saved_icons.items()):
                if progress_callback:
                    progress_callback(50 + int((idx / total_saved) * 50))

                if name in current_map:
                    icon_idx = current_map[name]
                    x_saved, y_saved = pos

                    x_new = int(x_saved * scale_x) if scaling_active else x_saved
                    y_new = int(y_saved * scale_y) if scaling_active else y_saved

                    # Bug 5 fix: use _pack_lparam to correctly handle negative coords
                    lparam = _pack_lparam(x_new, y_new)
                    win32gui.SendMessage(
                        self.hwnd_listview,
                        Win32Constants.LVM_SETITEMPOSITION,
                        icon_idx,
                        lparam,
                    )
                    moved_count += 1
                else:
                    skipped_count += 1

            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✓ Restored %n icon(s)", None, moved_count
                )
            )
            if skipped_count > 0:
                log_callback(
                    QCoreApplication.translate(
                        "DesktopIconManager",
                        "⚠ Skipped %n icon(s) (not found on desktop)",
                        None,
                        skipped_count,
                    )
                )

            if progress_callback:
                progress_callback(100)
            return True, saved_metadata

        except OSError as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error restoring (I/O): %1"
                ).replace("%1", str(e))
            )
            return False, saved_metadata
        except Exception as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error restoring: %1"
                ).replace("%1", str(e))
            )
            return False, saved_metadata
        finally:
            win32gui.SendMessage(self.hwnd_listview, win32con.WM_SETREDRAW, 1, 0)
            win32gui.InvalidateRect(self.hwnd_listview, None, True)
            if remote_memory and remote_memory != 0 and process_handle:
                win32process.VirtualFreeEx(
                    process_handle, remote_memory, 0, Win32Constants.MEM_RELEASE
                )
            if process_handle:
                win32api.CloseHandle(process_handle)

    def scramble_icons(
        self,
        log_callback: Callable[[str], None],
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        """Scramble icon positions randomly"""
        try:
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            margin = 100

            win32gui.SendMessage(self.hwnd_listview, win32con.WM_SETREDRAW, 0, 0)
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "Redrawing disabled for scrambling..."
                )
            )

            count = win32gui.SendMessage(
                self.hwnd_listview, Win32Constants.LVM_GETITEMCOUNT, 0, 0
            )
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "Found %n icon(s). Starting random positioning...",
                    None,
                    count,
                )
            )

            for i in range(count):
                if progress_callback:
                    progress_callback(int((i / count) * 100))

                rand_x = random.randint(margin, screen_width - margin)
                rand_y = random.randint(margin, screen_height - margin)

                lparam = _pack_lparam(rand_x, rand_y)
                win32gui.SendMessage(
                    self.hwnd_listview, Win32Constants.LVM_SETITEMPOSITION, i, lparam
                )

            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager",
                    "✓ Scrambled positions for %n icon(s).",
                    None,
                    count,
                )
            )

            if progress_callback:
                progress_callback(100)
            return True

        except Exception as e:
            log_callback(
                QCoreApplication.translate(
                    "DesktopIconManager", "✗ Error scrambling icons: %1"
                ).replace("%1", str(e))
            )
            return False
        finally:
            win32gui.SendMessage(self.hwnd_listview, win32con.WM_SETREDRAW, 1, 0)
            win32gui.InvalidateRect(self.hwnd_listview, None, True)


# NOTE: No module-level Win32 side-effects here.
# (Bug 4 fix: removed the SendMessageTimeout block that used to execute on import.)
