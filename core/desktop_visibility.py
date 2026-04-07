"""Desktop Icon Visibility Manager - Win32 API wrapper for showing/hiding desktop icons"""

import logging
from typing import Callable, Optional
import win32api
import win32con
import win32gui
import win32process
from ctypes import c_int, c_char_p, c_void_p, wintypes
from ctypes import windll, byref, POINTER

from PyQt6.QtCore import QCoreApplication


class DesktopVisibilityManager:
    """Manages showing/hiding of desktop icons using Win32 API"""

    def __init__(self):
        """Initialize the desktop visibility manager"""
        self.hwnd_progman = None
        self.hwnd_shelldll = None
        self._update_window_handles()

    def _update_window_handles(self) -> None:
        """Update cached window handles for desktop windows"""
        try:
            self.hwnd_progman = win32gui.FindWindow("Progman", None)
            if self.hwnd_progman:
                self.hwnd_shelldll = win32gui.FindWindowEx(
                    self.hwnd_progman, 0, "SHELLDLL_DefView", None
                )
        except Exception as e:
            logging.error("Error updating window handles: %s", e)

    def toggle_icon_visibility(
        self, log_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Toggle the visibility of desktop icons (show if hidden, hide if shown).
        Returns True if successful, False otherwise.
        """
        try:
            self._update_window_handles()

            if not self.hwnd_progman:
                error_msg = QCoreApplication.translate(
                    "DesktopVisibilityManager",
                    "Unable to locate the desktop window.",
                )
                if log_callback:
                    log_callback(f"✗ {error_msg}")
                logging.error(error_msg)
                return False

            # Get current visibility state
            is_visible = self._are_icons_visible()

            if is_visible:
                # Icons are visible → hide them
                return self._hide_icons(log_callback)
            else:
                # Icons are hidden → show them
                return self._show_icons(log_callback)

        except Exception as e:
            error_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "Error toggling desktop icon visibility: %1"
            ).replace("%1", str(e))
            if log_callback:
                log_callback(f"✗ {error_msg}")
            logging.error(error_msg)
            return False

    def show_icons(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Show desktop icons (no-op if already visible).
        Returns True if successful, False otherwise.
        """
        try:
            self._update_window_handles()

            if not self._are_icons_visible():
                # Icons are hidden → show them
                return self._show_icons(log_callback)
            else:
                # Icons already visible
                info_msg = QCoreApplication.translate(
                    "DesktopVisibilityManager", "Desktop icons are already visible."
                )
                if log_callback:
                    log_callback(f"ℹ {info_msg}")
                return True

        except Exception as e:
            error_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "Error showing desktop icons: %1"
            ).replace("%1", str(e))
            if log_callback:
                log_callback(f"✗ {error_msg}")
            logging.error(error_msg)
            return False

    def hide_icons(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """
        Hide desktop icons (no-op if already hidden).
        Returns True if successful, False otherwise.
        """
        try:
            self._update_window_handles()

            if self._are_icons_visible():
                # Icons are visible → hide them
                return self._hide_icons(log_callback)
            else:
                # Icons already hidden
                info_msg = QCoreApplication.translate(
                    "DesktopVisibilityManager", "Desktop icons are already hidden."
                )
                if log_callback:
                    log_callback(f"ℹ {info_msg}")
                return True

        except Exception as e:
            error_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "Error hiding desktop icons: %1"
            ).replace("%1", str(e))
            if log_callback:
                log_callback(f"✗ {error_msg}")
            logging.error(error_msg)
            return False

    def _are_icons_visible(self) -> bool:
        """
        Check if desktop icons are currently visible.
        Returns True if visible, False if hidden.
        """
        try:
            if not self.hwnd_shelldll:
                # If SHELLDLL_DefView doesn't exist, icons are likely hidden
                return False

            # Check if the SHELLDLL_DefView window is visible
            is_visible = win32gui.IsWindowVisible(self.hwnd_shelldll)
            return is_visible

        except Exception as e:
            logging.error("Error checking icon visibility: %s", e)
            # Default to True if we can't determine
            return True

    def _hide_icons(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Hide desktop icons by hiding the SHELLDLL_DefView window"""
        try:
            if not self.hwnd_shelldll:
                error_msg = QCoreApplication.translate(
                    "DesktopVisibilityManager",
                    "Unable to locate the desktop view window.",
                )
                if log_callback:
                    log_callback(f"✗ {error_msg}")
                return False

            # Hide the SHELLDLL_DefView window
            win32gui.ShowWindow(self.hwnd_shelldll, win32con.SW_HIDE)

            success_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "✓ Desktop icons hidden successfully."
            )
            if log_callback:
                log_callback(success_msg)
            logging.info("Desktop icons hidden")
            return True

        except Exception as e:
            error_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "Error hiding desktop icons: %1"
            ).replace("%1", str(e))
            if log_callback:
                log_callback(f"✗ {error_msg}")
            logging.error(error_msg)
            return False

    def _show_icons(self, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Show desktop icons by showing the SHELLDLL_DefView window"""
        try:
            self._update_window_handles()

            if not self.hwnd_shelldll:
                error_msg = QCoreApplication.translate(
                    "DesktopVisibilityManager",
                    "Unable to locate the desktop view window.",
                )
                if log_callback:
                    log_callback(f"✗ {error_msg}")
                return False

            # Show the SHELLDLL_DefView window
            win32gui.ShowWindow(self.hwnd_shelldll, win32con.SW_SHOW)

            success_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "✓ Desktop icons shown successfully."
            )
            if log_callback:
                log_callback(success_msg)
            logging.info("Desktop icons shown")
            return True

        except Exception as e:
            error_msg = QCoreApplication.translate(
                "DesktopVisibilityManager", "Error showing desktop icons: %1"
            ).replace("%1", str(e))
            if log_callback:
                log_callback(f"✗ {error_msg}")
            logging.error(error_msg)
            return False

    def get_current_visibility_state(self) -> Optional[bool]:
        """
        Get the current visibility state of desktop icons.
        Returns True if visible, False if hidden, None if unable to determine.
        """
        try:
            self._update_window_handles()
            return self._are_icons_visible()
        except Exception as e:
            logging.error("Error getting visibility state: %s", e)
            return None
