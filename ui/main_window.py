"""Main Window for Desktop Icon Backup Manager"""

import logging
from datetime import datetime
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any


from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QMessageBox,
    QApplication,
    QProgressBar,
    QDialog,
    QSystemTrayIcon,
    QMenu,
    QLineEdit,
    QComboBox,
    QSizePolicy,
    QToolButton,
    QFrame,
)

from PyQt6.QtCore import (
    QSettings,
    QTranslator,
    QLocale,
    QCoreApplication,
    QRect,
    QTimer,
    QUrl,
    Qt,
    QSize,
)
from PyQt6.QtGui import (
    QAction,
    QKeySequence,
    QIcon,
    QDesktopServices,
    QCursor,
    QPalette,
    QColor,
)

import win32gui
import win32con

from core.config import Config, resource_path
from core.icon_manager import DesktopIconManager
from core.desktop_visibility import DesktopVisibilityManager
from utils.threads import IconWorker
from utils.helpers import (
    get_display_metadata,
    get_readable_date,
    get_resolution_from_filename,
    parse_resolution_string,
)
from ui.backup_dialog import BackupManagerWindow, _ask
import ui.autohide as autohide
import ui.dialogs as dialogs
from ui.update_dialog import UpdateDialog
from ui.preview_widget import DiffPreviewWidget, make_legend_widget
from utils.logging_config import get_logger, attach_gui_handler, clear_log_file

logger = get_logger()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = DesktopIconManager()
        self.visibility_manager = DesktopVisibilityManager()
        self.current_resolution = get_display_metadata().get(
            "primary_resolution", self.tr("Unknown")
        )

        app_path = Path(os.path.abspath(sys.argv[0])).parent
        settings_file_path = app_path / "settings.ini"
        self.settings = QSettings(str(settings_file_path), QSettings.Format.IniFormat)
        self.log_path = app_path / "history.log"

        self.worker = None
        self.tray_icon = None
        self._force_quit = False
        self._autohide_worker = None

        # ── Auto-Hide timer ──────────────────────────────────────────────────
        self.autohide_timer = QTimer(self)
        self.autohide_timer.setSingleShot(True)
        self.autohide_timer.timeout.connect(self._on_autohide_timeout)

        self._autohide_remaining_sec = 0
        self._autohide_total_sec = 0
        self._autohide_notified = set()
        self.autohide_tick_timer = QTimer(self)
        self.autohide_tick_timer.setInterval(1000)
        self.autohide_tick_timer.timeout.connect(self._on_autohide_tick)

        # Countdown row widgets (created in setup_ui, always-present)
        self.autohide_status_frame = None
        self.autohide_status_label = None
        self.autohide_status_bar = None
        self.autohide_status_stop_btn = None
        # ─────────────────────────────────────────────────────────────────────

        self.create_tray_icon()

        self.DEFAULT_GEOMETRY = QRect(100, 100, 800, 650)

        self.setup_ui()

        # Attach structured logging to the GUI log area
        self._gui_log_handler = attach_gui_handler(self.log_area)

        self.setup_shortcuts()
        self.load_settings()

        # Start autohide timer if enabled and icons are currently visible
        if self.settings.value("autohide_enabled", False, type=bool):
            if self.visibility_manager.get_current_visibility_state():
                self._start_autohide_timer()

        # Refresh the countdown row so it reflects the initial state
        autohide.update_statusbar_countdown(self)

        if self.settings.value("auto_restore_on_startup", False, type=bool):
            QTimer.singleShot(1000, self.start_restore_latest)

        if self.settings.value("check_updates_on_startup", True, type=bool):
            QTimer.singleShot(Config.UPDATE_CHECK_DELAY_MS, self._silent_update_check)

    def create_tray_icon(self):
        icon = QIcon(resource_path("icon.ico"))
        self.tray_icon = QSystemTrayIcon(icon, self)

        tray_menu = QMenu()

        self.action_tray_save = QAction(self.tr("Quick Save"), self)
        self.action_tray_save.triggered.connect(
            lambda: self.start_save(description=self.tr("Quick Save (Tray)"))
        )
        tray_menu.addAction(self.action_tray_save)

        self.action_tray_restore = QAction(self.tr("Restore Latest"), self)
        self.action_tray_restore.triggered.connect(self.start_restore_latest)
        tray_menu.addAction(self.action_tray_restore)

        tray_menu.addSeparator()

        self.action_tray_toggle_icons = QAction(
            self.tr("Show/Hide Desktop Icons"), self
        )
        self.action_tray_toggle_icons.triggered.connect(self.toggle_icon_visibility)
        tray_menu.addAction(self.action_tray_toggle_icons)

        self.action_tray_show_icons = QAction(self.tr("Show Desktop Icons"), self)
        self.action_tray_show_icons.triggered.connect(self.show_desktop_icons)
        tray_menu.addAction(self.action_tray_show_icons)

        self.action_tray_hide_icons = QAction(self.tr("Hide Desktop Icons"), self)
        self.action_tray_hide_icons.triggered.connect(self.hide_desktop_icons)
        tray_menu.addAction(self.action_tray_hide_icons)

        tray_menu.addSeparator()

        self.action_tray_autohide = QAction(
            self.tr("⏱️ Auto-Hide Timer"), self, checkable=True
        )
        self.action_tray_autohide.triggered.connect(self._toggle_autohide)
        tray_menu.addAction(self.action_tray_autohide)

        tray_menu.addSeparator()

        self.action_tray_show = QAction(self.tr("Show Window"), self)
        self.action_tray_show.triggered.connect(self.show_window)
        tray_menu.addAction(self.action_tray_show)

        self.action_tray_exit = QAction(self.tr("Exit"), self)
        self.action_tray_exit.triggered.connect(self.exit_application)
        tray_menu.addAction(self.action_tray_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def exit_application(self):
        self._force_quit = True
        self.close()

    def setup_ui(self):
        self.setWindowTitle("Desktop Icon Backup Manager")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu(self.tr("&File"))

        self.action_scramble_icons = QAction(
            self.tr("Scramble Desktop Icons (Random)"), self
        )
        self.action_scramble_icons.setToolTip(
            self.tr(
                "Randomizes the position of all desktop icons after creating a mandatory backup."
            )
        )
        self.action_scramble_icons.triggered.connect(self.start_scramble)
        file_menu.addAction(self.action_scramble_icons)

        file_menu.addSeparator()

        # Desktop icons visibility submenu
        icons_menu = file_menu.addMenu(self.tr("👁️ Desktop Icons Visibility"))

        action_toggle_icons = QAction(self.tr("Show/Hide Desktop Icons"), self)
        action_toggle_icons.setShortcut(QKeySequence("Ctrl+H"))
        action_toggle_icons.setToolTip(
            self.tr("Toggle visibility of all desktop icons (Ctrl+H)")
        )
        action_toggle_icons.triggered.connect(self.toggle_icon_visibility)
        icons_menu.addAction(action_toggle_icons)

        action_show_icons = QAction(self.tr("Show Icons"), self)
        action_show_icons.triggered.connect(self.show_desktop_icons)
        icons_menu.addAction(action_show_icons)

        action_hide_icons = QAction(self.tr("Hide Icons"), self)
        action_hide_icons.triggered.connect(self.hide_desktop_icons)
        icons_menu.addAction(action_hide_icons)

        file_menu.addSeparator()

        self.action_remove_all = QAction(self.tr("Remove All Backups..."), self)
        self.action_remove_all.triggered.connect(self.confirm_and_delete_all_backups)
        file_menu.addAction(self.action_remove_all)

        file_menu.addSeparator()

        action_export = QAction(self.tr("📤 Export Backups..."), self)
        action_export.setToolTip(self.tr("Export backups to a folder or ZIP archive"))
        action_export.triggered.connect(self._open_backup_manager_for_export)
        file_menu.addAction(action_export)

        action_import = QAction(self.tr("📥 Import Backups..."), self)
        action_import.setToolTip(
            self.tr("Import backup files (.json) or a ZIP archive")
        )
        action_import.triggered.connect(self._import_backups_direct)
        file_menu.addAction(action_import)

        file_menu.addSeparator()
        action_exit = QAction(self.tr("E&xit"), self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.exit_application)
        file_menu.addAction(action_exit)

        settings_menu = menu_bar.addMenu(self.tr("&Settings"))

        action_open_settings = QAction(self.tr("Open Settings Menu"), self)
        action_open_settings.setShortcut(QKeySequence("Ctrl+,"))
        action_open_settings.triggered.connect(self.show_settings_menu)

        # Group 1: startup / exit behaviour
        self.action_auto_save = QAction(
            self.tr("Auto-Save on Exit"), self, checkable=True
        )
        self.action_auto_save.triggered.connect(
            lambda checked: self.settings.setValue("auto_save_on_exit", checked)
        )
        settings_menu.addAction(self.action_auto_save)

        self.action_auto_restore = QAction(
            self.tr("Auto-Restore on Startup"), self, checkable=True
        )
        self.action_auto_restore.triggered.connect(
            lambda checked: self.settings.setValue("auto_restore_on_startup", checked)
        )
        settings_menu.addAction(self.action_auto_restore)

        self.action_check_updates_on_startup = QAction(
            self.tr("Check for Updates on Startup"), self, checkable=True
        )
        self.action_check_updates_on_startup.triggered.connect(
            lambda checked: self.settings.setValue("check_updates_on_startup", checked)
        )
        settings_menu.addAction(self.action_check_updates_on_startup)

        settings_menu.addSeparator()

        # Group 2: restore behaviour
        self.action_adaptive_scaling = QAction(
            self.tr("Enable Adaptive Scaling on Restore"), self, checkable=True
        )
        self.action_adaptive_scaling.triggered.connect(
            lambda checked: self.settings.setValue("adaptive_scaling_enabled", checked)
        )
        settings_menu.addAction(self.action_adaptive_scaling)

        settings_menu.addSeparator()

        # Group 3: tray / window behaviour
        self.action_start_minimized = QAction(
            self.tr("Start Minimized to Tray"), self, checkable=True
        )
        self.action_start_minimized.triggered.connect(
            lambda checked: self.settings.setValue("start_minimized", checked)
        )
        settings_menu.addAction(self.action_start_minimized)

        self.action_close_to_tray = QAction(
            self.tr("Minimize to Tray on Close ('X' button)"), self, checkable=True
        )
        self.action_close_to_tray.triggered.connect(
            lambda checked: self.settings.setValue("close_to_tray", checked)
        )
        settings_menu.addAction(self.action_close_to_tray)

        settings_menu.addSeparator()

        # Group 4: cleanup
        self.cleanup_group = QMenu(self.tr("🗑️ Automatic Backup Cleanup Limit"), self)
        settings_menu.addMenu(self.cleanup_group)
        self.cleanup_actions = {}

        limits = {
            self.tr("Disabled (Keep All)"): 0,
            self.tr("Keep Last 5"): 5,
            self.tr("Keep Last 10"): 10,
            self.tr("Keep Last 25"): 25,
            self.tr("Keep Last 50"): 50,
        }

        for text, limit in limits.items():
            action = QAction(text, self, checkable=True)
            action.triggered.connect(
                lambda checked, l=limit: self._set_cleanup_limit(l)
            )
            self.cleanup_group.addAction(action)
            self.cleanup_actions[limit] = action

        settings_menu.addSeparator()

        # Group 5: auto-hide desktop icons
        self.autohide_group = QMenu(self.tr("⏱️ Auto-Hide Desktop Icons"), self)
        settings_menu.addMenu(self.autohide_group)

        self.action_autohide_enabled = QAction(
            self.tr("Enable Auto-Hide Timer"), self, checkable=True
        )
        self.action_autohide_enabled.triggered.connect(self._toggle_autohide)
        self.autohide_group.addAction(self.action_autohide_enabled)

        self.autohide_group.addSeparator()

        self.autohide_time_group = QMenu(self.tr("Hide After..."), self)
        self.autohide_group.addMenu(self.autohide_time_group)
        self.autohide_time_actions = {}

        # Values are in seconds
        autohide_intervals = {
            self.tr("30 seconds"): 30,
            self.tr("1 minute"): 60,
            self.tr("2 minutes"): 120,
            self.tr("5 minutes"): 300,
            self.tr("10 minutes"): 600,
            self.tr("15 minutes"): 900,
            self.tr("30 minutes"): 1800,
        }

        for text, seconds in autohide_intervals.items():
            action = QAction(text, self, checkable=True)
            action.triggered.connect(
                lambda checked, s=seconds: self._set_autohide_seconds(s)
            )
            self.autohide_time_group.addAction(action)
            self.autohide_time_actions[seconds] = action

        self.autohide_time_group.addSeparator()

        self.action_autohide_custom = QAction(
            self.tr("Custom..."), self, checkable=True
        )
        self.action_autohide_custom.triggered.connect(
            lambda checked: self._ask_custom_autohide_time()
        )
        self.autohide_time_group.addAction(self.action_autohide_custom)

        self.autohide_group.addSeparator()

        self.action_autohide_backup = QAction(
            self.tr("Backup Before Auto-Hide"), self, checkable=True
        )
        self.action_autohide_backup.triggered.connect(
            lambda checked: self.settings.setValue(
                "autohide_backup_before_hide", checked
            )
        )
        self.autohide_group.addAction(self.action_autohide_backup)

        self.action_autohide_notify = QAction(
            self.tr("Notify Before Hiding (1 min / 10 s)"), self, checkable=True
        )
        self.action_autohide_notify.triggered.connect(
            lambda checked: self.settings.setValue("autohide_notify_enabled", checked)
        )
        self.autohide_group.addAction(self.action_autohide_notify)

        settings_menu.addSeparator()

        # Group 6: colour theme
        self.theme_group = QMenu(self.tr("🎨 Theme"), self)
        settings_menu.addMenu(self.theme_group)

        self._theme_actions: dict[str, QAction] = {}
        _theme_options = [
            ("system", self.tr("Use System Setting")),
            ("light", self.tr("Light")),
            ("dark", self.tr("Dark")),
        ]
        for _mode, _label in _theme_options:
            _act = QAction(_label, self, checkable=True)
            _act.triggered.connect(lambda checked, m=_mode: self._set_theme_mode(m))
            self.theme_group.addAction(_act)
            self._theme_actions[_mode] = _act

        help_menu = menu_bar.addMenu(self.tr("&Help"))

        action_manual = QAction(self.tr("Online User Manual"), self)
        action_manual.setShortcut(QKeySequence("F1"))
        action_manual.triggered.connect(self.open_online_manual)
        help_menu.addAction(action_manual)

        help_menu.addSeparator()

        action_shortcuts = QAction(self.tr("Keyboard Shortcuts"), self)
        action_shortcuts.triggered.connect(self.show_shortcuts_dialog)
        help_menu.addAction(action_shortcuts)

        action_stats = QAction(self.tr("Statistics Dashboard"), self)
        action_stats.triggered.connect(self.show_stats_dialog)
        help_menu.addAction(action_stats)

        help_menu.addSeparator()

        action_check_updates = QAction(self.tr("Check for Updates..."), self)
        action_check_updates.triggered.connect(self.show_update_dialog)
        help_menu.addAction(action_check_updates)

        help_menu.addSeparator()

        action_about = QAction(self.tr("&About"), self)
        action_about.triggered.connect(self.show_about_dialog)
        help_menu.addAction(action_about)

        help_menu.addSeparator()

        action_kofi = QAction(self.tr("Support on Ko-fi..."), self)
        action_kofi.triggered.connect(self.open_kofi)
        help_menu.addAction(action_kofi)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)

        # ── Auto-Hide countdown row (shown only when the timer is armed) ──
        self.autohide_status_frame = QFrame()
        self.autohide_status_frame.setObjectName("autohideStatusFrame")
        self.autohide_status_frame.setVisible(False)
        self.autohide_status_frame.setStyleSheet(
            "QFrame#autohideStatusFrame {"
            " background-color: rgba(0, 120, 215, 180);"
            " border: 1px solid #0078D7;"
            " border-radius: 6px;"
            "}"
        )

        ah_row = QHBoxLayout(self.autohide_status_frame)
        ah_row.setContentsMargins(10, 6, 6, 6)
        ah_row.setSpacing(10)

        self.autohide_status_label = QLabel()
        self.autohide_status_label.setStyleSheet(
            "QLabel { color: palette(window-text); font-weight: 600;"
            " background: transparent; border: none; }"
        )
        ah_row.addWidget(self.autohide_status_label)

        self.autohide_status_bar = QProgressBar()
        self.autohide_status_bar.setTextVisible(False)
        self.autohide_status_bar.setFixedHeight(8)
        self.autohide_status_bar.setMinimumWidth(160)
        self.autohide_status_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.autohide_status_bar.setStyleSheet(
            "QProgressBar { border: 1px solid rgba(255, 255, 255, 60);"
            " border-radius: 4px; background-color: rgba(0, 0, 0, 60); }"
            "QProgressBar::chunk { background-color: #4DA3E8; border-radius: 3px; }"
        )
        ah_row.addWidget(self.autohide_status_bar, 1)

        from ui.autohide_icons import make_stop_icon
        from PyQt6.QtGui import QColor, QPalette

        # Pick an icon color that contrasts with the banner fill on either theme.
        # In dark mode the translucent blue fill reads dark → white icon wins.
        # In light mode the fill reads pale → a darker blue icon is visible.
        app_palette = QApplication.palette()
        is_dark = app_palette.color(QPalette.ColorRole.Window).value() < 128
        icon_color = QColor("#FFFFFF") if is_dark else QColor("#0C447C")
        self.autohide_status_stop_btn = QToolButton()
        self.autohide_status_stop_btn.setIcon(make_stop_icon(18, icon_color))
        self.autohide_status_stop_btn.setIconSize(QSize(18, 18))
        self.autohide_status_stop_btn.setFixedSize(26, 26)
        self.autohide_status_stop_btn.setAutoRaise(True)
        self.autohide_status_stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.autohide_status_stop_btn.setToolTip(self.tr("Disable Auto-Hide"))
        self.autohide_status_stop_btn.setStyleSheet(
            "QToolButton { border: none; background: transparent;"
            " border-radius: 13px; padding: 0; }"
            "QToolButton:hover { background: #CC0000; }"
        )
        self.autohide_status_stop_btn.clicked.connect(
            lambda: self._toggle_autohide(False)
        )
        ah_row.addWidget(self.autohide_status_stop_btn)

        layout.addWidget(self.autohide_status_frame)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.save_tag_input = QLineEdit()
        self.save_tag_input.setPlaceholderText(
            self.tr("Optional: Enter a descriptive tag/description...")
        )

        # Named-profile preset combo — selecting an entry copies the name into
        # the tag field so the user can use it as-is or refine it further.
        self.profile_combo = QComboBox()
        self.profile_combo.setToolTip(
            self.tr("Select a profile to auto-fill the tag field")
        )
        self._populate_profile_combo()
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)

        tag_input_row = QHBoxLayout()
        tag_input_row.addWidget(QLabel(self.tr("Save Tag:")))
        tag_input_row.addWidget(self.save_tag_input, 1)
        tag_input_row.addWidget(self.profile_combo)
        layout.addLayout(tag_input_row)

        action_buttons_row = QHBoxLayout()
        action_buttons_row.setSpacing(10)

        self.btn_save_latest = QPushButton(self.tr("💾 SAVE QUICK BACKUP"))
        self.btn_save_latest.setMinimumHeight(50)

        self.btn_save_latest.setToolTip(
            self.tr(
                "Save current desktop icon positions to a new file, using the tag above.\n\nShortcut: Ctrl+S"
            )
        )

        self.btn_save_latest.clicked.connect(self.quick_save_with_tag)
        self.btn_save_latest.setObjectName("saveButton")

        self.btn_restore_latest = QPushButton(self.tr("↺ RESTORE LATEST"))
        self.btn_restore_latest.setMinimumHeight(50)
        self.btn_restore_latest.setToolTip(
            self.tr("Restore icon positions from the LATEST backup file found.")
        )
        self.btn_restore_latest.clicked.connect(self.start_restore_latest)
        self.btn_restore_latest.setObjectName("restoreButton")

        self.btn_restore_select = QPushButton("↺ BACKUP MANAGER")
        self.btn_restore_select.setMinimumHeight(50)

        self.btn_restore_select.setToolTip(
            self.tr(
                "Opens a window to select a specific backup file to restore or delete.\n\nShortcut: Ctrl+M"
            )
        )

        self.btn_restore_select.clicked.connect(self.open_backup_manager)
        self.btn_restore_select.setObjectName("backupManagerButton")

        self.btn_toggle_icons = QPushButton(self.tr("👁️ SHOW/HIDE ICONS"))
        self.btn_toggle_icons.setMinimumHeight(50)
        self.btn_toggle_icons.setToolTip(
            self.tr("Show or hide all desktop icons.\n\nShortcut: Ctrl+H")
        )
        self.btn_toggle_icons.clicked.connect(self.toggle_icon_visibility)
        self.btn_toggle_icons.setObjectName("toggleIconsButton")

        action_buttons_row.addWidget(self.btn_save_latest, 1)
        action_buttons_row.addWidget(self.btn_restore_latest, 1)
        action_buttons_row.addWidget(self.btn_restore_select, 1)
        action_buttons_row.addWidget(self.btn_toggle_icons, 1)

        layout.addLayout(action_buttons_row)

        layout.addWidget(QLabel(self.tr("Activity Log:")))

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(300)
        self.log_area.setMaximumHeight(600)
        layout.addWidget(self.log_area)

        log_button_layout = QHBoxLayout()

        self.status_label = QLabel(
            self.tr("Current Resolution: %1").replace("%1", self.current_resolution)
        )
        log_button_layout.addWidget(self.status_label)

        log_button_layout.addStretch(1)

        kofi_label = QLabel(
            f'<a href="https://ko-fi.com/mapi68" style="color: #FF5E5B; text-decoration: none;">{self.tr("Support on Ko-fi")}</a>'
        )
        kofi_label.setOpenExternalLinks(True)
        kofi_label.setToolTip("https://ko-fi.com/mapi68")
        log_button_layout.addWidget(kofi_label)

        self.btn_clear_log = QPushButton(self.tr("Clear Log"))
        self.btn_clear_log.clicked.connect(self.clear_log)
        self.btn_clear_log.setMaximumWidth(150)
        self.btn_clear_log.setObjectName("clearLogButton")
        log_button_layout.addWidget(self.btn_clear_log)

        layout.addLayout(log_button_layout)

        # Styles are loaded from styles/theme.qss at application level

    def show_settings_menu(self):
        menu_bar = self.menuBar()
        settings_menu = None

        for action in menu_bar.actions():
            if action.text() == self.tr("&Settings"):
                settings_menu = action.menu()
                break

        if settings_menu:
            cursor_pos = QCursor.pos()
            settings_menu.exec(cursor_pos)
        else:
            self.log(self.tr("Settings menu not found"))

    def open_kofi(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/mapi68"))

    def open_online_manual(self):
        manual_url = QUrl(
            "https://mapi68.github.io/desktop-icon-backup-manager/manual.pdf"
        )
        success = QDesktopServices.openUrl(manual_url)

        if success:
            self.log(self.tr("Opening online user manual in browser..."))
        else:
            self.log(self.tr("✗ Failed to open manual URL"))
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr(
                    "Could not open the online manual.\n\nPlease visit manually:\n%1"
                ).replace("%1", manual_url.toString()),
            )

    def setup_shortcuts(self):

        save_shortcut = QAction(self.tr("Save"), self)
        save_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        save_shortcut.triggered.connect(
            lambda: self.start_save(description=self.tr("Quick Backup (Shortcut)"))
        )
        self.addAction(save_shortcut)

        manager_shortcut = QAction("Backup Manager", self)
        manager_shortcut.setShortcut(QKeySequence("Ctrl+M"))
        manager_shortcut.triggered.connect(self.open_backup_manager)
        self.addAction(manager_shortcut)

    def load_settings(self):
        self.action_start_minimized.setChecked(
            self.settings.value("start_minimized", False, type=bool)
        )
        self.action_auto_save.setChecked(
            self.settings.value("auto_save_on_exit", False, type=bool)
        )
        self.action_auto_restore.setChecked(
            self.settings.value("auto_restore_on_startup", False, type=bool)
        )
        self.action_adaptive_scaling.setChecked(
            self.settings.value("adaptive_scaling_enabled", False, type=bool)
        )
        self.action_close_to_tray.setChecked(
            self.settings.value("close_to_tray", False, type=bool)
        )
        self.action_check_updates_on_startup.setChecked(
            self.settings.value("check_updates_on_startup", True, type=bool)
        )

        current_limit = self.settings.value("cleanup_limit", 0, type=int)
        self._update_cleanup_menu_check(current_limit)

        # Theme mode
        current_theme = self.settings.value("theme_mode", "system")
        self._update_theme_menu_check(current_theme)

        # Auto-hide settings
        autohide_on = self.settings.value("autohide_enabled", False, type=bool)
        self.action_autohide_enabled.setChecked(autohide_on)
        self.action_tray_autohide.setChecked(autohide_on)
        current_autohide_sec = self.settings.value("autohide_seconds", 300, type=int)
        self._update_autohide_time_menu_check(current_autohide_sec)
        self.action_autohide_backup.setChecked(
            self.settings.value("autohide_backup_before_hide", True, type=bool)
        )
        self.action_autohide_notify.setChecked(
            self.settings.value("autohide_notify_enabled", True, type=bool)
        )

        geometry = self.settings.value("geometry", self.DEFAULT_GEOMETRY, type=QRect)
        self.setGeometry(geometry)

    def _set_cleanup_limit(self, limit: int):
        self.settings.setValue("cleanup_limit", limit)
        self._update_cleanup_menu_check(limit)
        self.log(
            self.tr(
                "Automatic cleanup limit set to: %n backup(s) (0 = Disabled).",
                None,
                limit,
            )
        )

    def _update_cleanup_menu_check(self, current_limit: int):
        for limit, action in self.cleanup_actions.items():
            action.setChecked(limit == current_limit)

    # ── Colour Theme ─────────────────────────────────────────────────────────

    def _set_theme_mode(self, mode: str) -> None:
        """Save *mode* and apply the palette immediately (no restart needed)."""
        self.settings.setValue("theme_mode", mode)
        self._update_theme_menu_check(mode)
        # Import lazily to avoid a circular import with main.py
        from main import apply_theme

        apply_theme(QApplication.instance(), mode)
        _mode_labels = {
            "system": self.tr("System"),
            "light": self.tr("Light"),
            "dark": self.tr("Dark"),
        }
        self.log(
            QCoreApplication.translate(
                "MainWindow",
                "Theme changed to: %1",
            ).replace("%1", _mode_labels.get(mode, mode))
        )

    def _update_theme_menu_check(self, current_mode: str) -> None:
        for mode, action in self._theme_actions.items():
            action.setChecked(mode == current_mode)

    # ── Auto-Hide Desktop Icons (logica in ui/autohide.py) ──────────────────

    def _toggle_autohide(self, checked: bool):
        autohide.toggle_autohide(self, checked)

    def _set_autohide_seconds(self, seconds: int):
        autohide.set_autohide_seconds(self, seconds)

    def _update_autohide_time_menu_check(self, current_seconds: int):
        autohide.update_autohide_time_menu_check(self, current_seconds)

    def _ask_custom_autohide_time(self):
        autohide.ask_custom_autohide_time(self)

    def _format_duration(self, seconds: int) -> str:
        return autohide.format_duration(self, seconds)

    def _start_autohide_timer(self):
        autohide.start_autohide_timer(self)

    def _stop_autohide_timer(self):
        autohide.stop_autohide_timer(self)

    def _on_autohide_tick(self):
        autohide.on_autohide_tick(self)

    def _update_tray_autohide_tooltip(self):
        autohide.update_tray_autohide_tooltip(self)

    def _on_autohide_timeout(self):
        autohide.on_autohide_timeout(self)

    def _on_autohide_backup_done(self, success: bool, metadata):
        autohide.on_autohide_backup_done(self, success, metadata)

    def _do_autohide_icons(self):
        autohide.do_autohide_icons(self)

    def _restart_autohide_if_icons_visible(self):
        autohide.restart_autohide_if_icons_visible(self)

    # ─────────────────────────────────────────────────────────────────────────

    # ─────────────────────────────────────────────────────────────────────────

    def log(self, message: str):
        """Log a message via the structured logger (file + GUI + console)."""
        logger.info(message)

        if not self.isVisible() and ("✗" in message or "CRITICAL ERROR" in message):
            self.tray_icon.showMessage(
                self.tr("Desktop Icon Manager"),
                message,
                QSystemTrayIcon.MessageIcon.Warning,
                5000,
            )

    def clear_log(self):
        """Clear the log area and the history file."""
        self.log_area.clear()
        clear_log_file(self.log_path)

    def toggle_buttons(self, enabled: bool):
        self.btn_save_latest.setEnabled(enabled)
        self.btn_restore_latest.setEnabled(enabled)
        self.btn_restore_select.setEnabled(enabled)
        self.action_remove_all.setEnabled(enabled)
        self.btn_clear_log.setEnabled(enabled)
        self.action_scramble_icons.setEnabled(enabled)

        if self.tray_icon:
            self.action_tray_save.setEnabled(enabled)
            self.action_tray_restore.setEnabled(enabled)

    def show_progress(self, show: bool):
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setValue(0)

    def update_progress(self, value: int):
        self.progress_bar.setValue(value)

    def open_backup_manager(self):
        manager_window = BackupManagerWindow(self.manager, self)
        manager_window.restore_requested.connect(self.start_restore_specific)
        manager_window.list_changed_signal.connect(
            lambda: self.log(self.tr("Backup list updated (item deleted)."))
        )
        manager_window.exec()

    def _open_backup_manager_for_export(self):
        """Open Backup Manager and trigger the export flow directly."""
        manager_window = BackupManagerWindow(self.manager, self)
        manager_window.restore_requested.connect(self.start_restore_specific)
        manager_window.list_changed_signal.connect(
            lambda: self.log(self.tr("Backup list updated."))
        )
        # Trigger export immediately after the dialog is shown
        QTimer.singleShot(0, manager_window.export_backups)
        manager_window.exec()

    def _import_backups_direct(self):
        """Open Backup Manager and trigger the import flow directly."""
        manager_window = BackupManagerWindow(self.manager, self)
        manager_window.restore_requested.connect(self.start_restore_specific)
        manager_window.list_changed_signal.connect(
            lambda: self.log(self.tr("Backup list updated (imported)."))
        )
        QTimer.singleShot(0, manager_window.import_backups)
        manager_window.exec()

    # ── Named profiles ────────────────────────────────────────────────────────

    def _populate_profile_combo(self) -> None:
        """Fill the profile preset combo with the built-in named profiles."""
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        # First entry: placeholder — selecting it does nothing
        self.profile_combo.addItem(self.tr("— Profiles —"), None)
        profiles = [
            self.tr("Work"),
            self.tr("Gaming"),
            self.tr("Presentation"),
            self.tr("Dev / Coding"),
            self.tr("Meeting"),
            self.tr("Home"),
            self.tr("Office"),
            self.tr("Laptop"),
            self.tr("Docked / External Monitor"),
            self.tr("Clean Desktop"),
            self.tr("Pre-Update"),
            self.tr("Pre-Reboot"),
            self.tr("Favourite"),
            self.tr("Test"),
        ]
        for name in profiles:
            self.profile_combo.addItem(name, name)
        self.profile_combo.blockSignals(False)

    def _on_profile_selected(self, index: int) -> None:
        """Copy the selected profile name into the tag field (index 0 = placeholder)."""
        if index <= 0:
            return
        name = self.profile_combo.itemData(index)
        if name:
            self.save_tag_input.setText(name)
        # Reset to placeholder so re-selecting the same item still triggers
        self.profile_combo.blockSignals(True)
        self.profile_combo.setCurrentIndex(0)
        self.profile_combo.blockSignals(False)

    # ─────────────────────────────────────────────────────────────────────────

    def quick_save_with_tag(self):
        tag = self.save_tag_input.text().strip()
        description = tag if tag else self.tr("Quick Backup")
        self.start_save(description=description)

    def start_restore_specific(self, filename: str):
        if self.worker and self.worker.isRunning():
            return
        self._start_restore(filename)

    def show_about_dialog(self):
        dialogs.show_about_dialog(self)

    def confirm_and_delete_all_backups(self):
        backup_count = len(self.manager.get_all_backup_filenames())

        if backup_count == 0:
            self.log(self.tr("No backup files found to delete."))
            QMessageBox.information(
                self,
                self.tr("No Backups Found"),
                self.tr("There are no backup files to delete."),
            )
            return

        if _ask(
            self,
            self.tr("WARNING: Delete All Backups"),
            self.tr(
                "Are you absolutely sure you want to permanently delete all desktop icon backup files?\n\nThis action cannot be undone!"
            ),
            self.tr("Yes"),
            self.tr("No"),
        ):
            self.log(self.tr("Starting deletion of all backup files..."))
            self.toggle_buttons(False)
            success = self.manager.delete_all_backups(self.log)
            self.toggle_buttons(True)

            if success:
                QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("All backup files have been successfully deleted."),
                )
            else:
                QMessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr(
                        "Some files could not be deleted. Check the Activity Log for details."
                    ),
                )

    def start_save(self, description: Optional[str] = None):
        if self.worker and self.worker.isRunning():
            return
        cleanup_limit = self.settings.value("cleanup_limit", 0, type=int)

        self.log(self.tr("Starting new timestamped backup..."))
        if description:
            self.log(self.tr("  (Tag: %1)").replace("%1", str(description)))

        self.toggle_buttons(False)
        self.show_progress(True)
        self.statusBar().showMessage(self.tr("Saving..."))

        self.worker = IconWorker(
            "save",
            description=description,
            max_backup_count=cleanup_limit,
            manager=self.manager,
        )
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_operation_finished)
        self.worker.start()

    def start_restore_latest(self):
        if self.worker and self.worker.isRunning():
            return
        latest_backup_file = self.manager.get_latest_backup_filename()

        if not latest_backup_file:
            QMessageBox.warning(
                self, self.tr("Error"), self.tr("No backup files found to restore!")
            )
            self.log(self.tr("✗ Restore failed: No backup files found."))
            return

        self._show_restore_preview_dialog(latest_backup_file)

    def _show_restore_preview_dialog(self, filename: str):
        """Show a restore confirmation dialog with a live diff preview."""
        filepath = os.path.join(Config.BACKUP_DIR, filename)
        formatted_date = get_readable_date(filename)
        resolution = get_resolution_from_filename(filename)

        description = self.tr("N/A")
        icon_count = self.tr("N/A")
        saved_icons = {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                description = data.get("description", self.tr("N/A"))
                icon_count = data.get("icon_count", self.tr("N/A"))
                saved_icons = data.get("icons", {})
        except Exception:
            description = self.tr("N/A (Old Format)")

        try:
            current_icons = self.manager.get_current_icon_positions()
        except Exception:
            current_icons = {}

        res_tuple = parse_resolution_string(resolution) or (1920, 1080)

        # Count what will actually change
        moved = sum(
            1
            for name, pos in saved_icons.items()
            if name in current_icons
            and (
                abs(pos[0] - current_icons[name][0]) > 4
                or abs(pos[1] - current_icons[name][1]) > 4
            )
        )
        unchanged = sum(
            1
            for name, pos in saved_icons.items()
            if name in current_icons
            and abs(pos[0] - current_icons[name][0]) <= 4
            and abs(pos[1] - current_icons[name][1]) <= 4
        )
        missing = sum(1 for name in saved_icons if name not in current_icons)

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Confirm Restore — Live Preview"))
        dialog.setMinimumSize(900, 580)
        dialog.resize(1000, 640)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # Info header
        info_html = (
            f"<b>{self.tr('File')}:</b> {filename}&nbsp;&nbsp;"
            f"<b>{self.tr('Resolution')}:</b> {resolution}&nbsp;&nbsp;"
            f"<b>{self.tr('Icons')}:</b> {icon_count}&nbsp;&nbsp;"
            f"<b>{self.tr('Tag')}:</b> {description}&nbsp;&nbsp;"
            f"<b>{self.tr('Timestamp')}:</b> {formatted_date}"
        )
        info_label = QLabel(info_html)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "border: 1px solid palette(mid); border-radius: 4px;"
            " padding: 8px; font-family: 'Segoe UI'; font-size: 11px;"
        )
        layout.addWidget(info_label)

        # Diff summary bar
        summary_html = (
            f"<span style='color:#FF9800;'>⬤</span> <b>{moved}</b> {self.tr('will move')}&nbsp;&nbsp;&nbsp;"
            f"<span style='color:#0078D7;'>⬤</span> <b>{unchanged}</b> {self.tr('already in place')}&nbsp;&nbsp;&nbsp;"
            f"<span style='color:#4CAF50;'>⬤</span> <b>{missing}</b> {self.tr('not on desktop')}"
        )
        summary_label = QLabel(summary_html)
        summary_label.setStyleSheet(
            "font-family: 'Segoe UI'; font-size: 12px; padding: 4px 0px;"
        )
        layout.addWidget(summary_label)

        # Preview label
        preview_title = QLabel(self.tr("Layout Preview (saved positions vs current):"))
        preview_title.setStyleSheet(
            "font-family: 'Segoe UI'; font-size: 10px; font-weight: bold;"
        )
        layout.addWidget(preview_title)

        # Preview canvas + legend side by side
        preview_row = QHBoxLayout()
        preview_widget = DiffPreviewWidget()
        preview_widget.update_preview(saved_icons, current_icons, res_tuple)
        preview_row.addWidget(preview_widget, stretch=1)

        legend = make_legend_widget()
        legend.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        legend.setMinimumWidth(320)
        preview_row.addWidget(legend)
        layout.addLayout(preview_row, stretch=1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_restore = QPushButton(self.tr("↺ Restore"))
        btn_restore.setMinimumHeight(38)
        btn_restore.setStyleSheet(
            "QPushButton { color: white; background-color: #CC0000; font-weight: bold;"
            " border-radius: 5px; padding: 6px 18px; font-size: 13px; }"
            "QPushButton:hover { background-color: #aa0000; }"
        )
        btn_cancel = QPushButton(self.tr("Cancel"))
        btn_cancel.setMinimumHeight(38)

        btn_row.addStretch(1)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_restore)
        layout.addLayout(btn_row)

        btn_restore.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._start_restore(filename)

    def _start_restore(self, filename: Optional[str] = None):
        enable_scaling = self.settings.value(
            "adaptive_scaling_enabled", False, type=bool
        )

        self.log(
            self.tr("Starting restore from backup '%1'...").replace(
                "%1", str(filename if filename else self.tr("latest"))
            )
        )
        self.toggle_buttons(False)
        self.show_progress(True)
        self.statusBar().showMessage(self.tr("Restoring..."))

        self.worker = IconWorker(
            "restore", filename, enable_scaling=enable_scaling, manager=self.manager
        )
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.on_operation_finished)
        self.worker.start()

    def start_scramble(self):
        if self.worker and self.worker.isRunning():
            return
        if _ask(
            self,
            self.tr("Confirm Scramble"),
            self.tr(
                "Are you sure you want to randomize the positions of ALL desktop icons?\n\n**A mandatory backup will be created first**.\n\nDo you want to proceed?"
            ),
            self.tr("Yes"),
            self.tr("No"),
        ):
            self.log(self.tr("Starting desktop icon scrambling (randomization)..."))
            self.toggle_buttons(False)
            self.show_progress(True)
            self.statusBar().showMessage(self.tr("Scrambling icons..."))

            self.worker = IconWorker("scramble", manager=self.manager)
            self.worker.log_signal.connect(self.log)
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.finished_signal.connect(self.on_operation_finished)
            self.worker.start()

    def on_operation_finished(self, success: bool, saved_metadata: Optional[Dict]):
        # BUG 1 fix: capture mode locally before clearing self.worker
        mode = self.worker.mode if self.worker else "unknown"
        self.worker = None

        if mode == "restore" and success:
            self._check_display_metadata(saved_metadata)

        # ── Increment persistent statistics counters ──────────────────────
        if success:
            if mode == "restore":
                n = self.settings.value("stats/total_restores_performed", 0, type=int)
                self.settings.setValue("stats/total_restores_performed", n + 1)
            elif mode == "scramble":
                n = self.settings.value("stats/total_scrambles", 0, type=int)
                self.settings.setValue("stats/total_scrambles", n + 1)
            elif mode == "save":
                n = self.settings.value("stats/total_saves_performed", 0, type=int)
                self.settings.setValue("stats/total_saves_performed", n + 1)

        self.toggle_buttons(True)
        self.show_progress(False)

        if success:
            self.statusBar().showMessage(
                self.tr("Operation completed successfully"), 3000
            )
            if mode != "save":
                QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("Operation completed successfully! (%1)").replace(
                        "%1", str(mode.capitalize())
                    ),
                )
            if not self.isVisible():
                self.tray_icon.showMessage(
                    self.tr("Desktop Icon Manager"),
                    self.tr("%1 successful!").replace("%1", str(mode.capitalize())),
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )
            # After a restore or scramble the icons are visible → restart timer
            if mode in ("restore", "scramble"):
                self._restart_autohide_if_icons_visible()
        else:
            self.statusBar().showMessage(self.tr("Operation failed"), 3000)
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Operation failed (%1). Check the log for details.").replace(
                    "%1", str(mode.capitalize())
                ),
            )

    def _check_display_metadata(self, saved_metadata: Dict):
        if not saved_metadata:
            return
        current_metadata = get_display_metadata()
        saved_count = saved_metadata.get("monitor_count")
        current_count = current_metadata.get("monitor_count")

        if saved_count is None or current_count is None:
            self.log(self.tr("⚠ Warning: Display metadata missing or incomplete."))
            return

        if saved_count != current_count:
            self.log(
                self.tr(
                    "⚠ Warning: Saved (%n monitor(s)) vs Current (%1 monitor(s)).",
                    None,
                    saved_count,
                ).replace("%1", str(current_count))
            )
            QMessageBox.warning(
                self,
                self.tr("Monitor Mismatch Warning"),
                self.tr(
                    "The layout was saved with %1 monitor(s), but you currently have %2 monitor(s) connected.\n\nIcon positions have been restored, but they may be inaccurate."
                )
                .replace("%1", str(saved_count))
                .replace("%2", str(current_count)),
            )
            return

        saved_screens = saved_metadata.get("screens", [])
        current_screens = current_metadata.get("screens", [])

        mismatch_found = False
        if len(saved_screens) == len(current_screens):
            for s_screen, c_screen in zip(saved_screens, current_screens):
                if s_screen.get("width") != c_screen.get("width") or s_screen.get(
                    "height"
                ) != c_screen.get("height"):
                    mismatch_found = True
                    break

        if mismatch_found:
            self.log(
                self.tr("⚠ Warning: Screen resolutions do not match the saved layout.")
            )
            QMessageBox.warning(
                self,
                self.tr("Resolution Mismatch Warning"),
                self.tr(
                    "The screen resolutions for one or more monitors do not match the saved layout.\n\nIcon positions have been restored, but they may be inaccurate."
                ),
            )

    def _run_final_cleanup(self):
        if self.isVisible():
            self.settings.setValue("geometry", self.geometry())

        if self.action_auto_save.isChecked():
            # Skip auto-save if a quick save was performed in the last 10 seconds
            _skip_auto_save = False
            try:
                import os as _os
                import json as _json
                from datetime import datetime as _datetime

                _backup_files = [
                    f for f in _os.listdir(Config.BACKUP_DIR) if f.endswith(".json")
                ]
                if _backup_files:
                    _backup_files.sort(reverse=True)
                    _latest_path = _os.path.join(Config.BACKUP_DIR, _backup_files[0])
                    with open(_latest_path, "r", encoding="utf-8") as _f:
                        _latest_data = _json.load(_f)
                    _ts_str = _latest_data.get("timestamp", "")
                    if _ts_str:
                        _ts = _datetime.fromisoformat(_ts_str)
                        # Strip tzinfo if present to compare as naive local time
                        if _ts.tzinfo is not None:
                            _ts = _ts.replace(tzinfo=None)
                        _now = _datetime.now()
                        _seconds_ago = (_now - _ts).total_seconds()
                        if _seconds_ago <= Config.AUTO_SAVE_SKIP_SECONDS:
                            _skip_auto_save = True
                            if self.isVisible():
                                self.log(
                                    self.tr(
                                        "Auto-Save skipped: a Quick Save was performed less than 10 seconds ago."
                                    )
                                )
            except Exception:
                pass  # If anything goes wrong, proceed normally with auto-save

            if not _skip_auto_save:
                if self.isVisible():
                    self.log(
                        self.tr(
                            "Auto-Save on Exit enabled. Performing silent backup..."
                        )
                    )
                cleanup_limit = self.settings.value("cleanup_limit", 0, type=int)
                from PyQt6.QtWidgets import QProgressDialog

                progress = QProgressDialog(
                    self.tr("Auto-Save icon layout…"),
                    None,  # no cancel button
                    0,
                    0,  # indeterminate
                    self,
                )
                progress.setWindowTitle(self.tr("Please wait"))
                progress.setMinimumDuration(0)
                progress.setValue(0)
                QApplication.processEvents()
                self.manager.save(
                    lambda msg: print(f"{self.tr('Auto-Save Log')}: {msg}"),
                    description=self.tr("Auto-Save on Exit"),
                    max_backup_count=cleanup_limit,
                )
                progress.close()

    def closeEvent(self, event):
        close_to_tray = self.action_close_to_tray.isChecked()
        is_pyinstaller = getattr(sys, "frozen", False)

        if close_to_tray and not self._force_quit and self.isVisible():
            self.settings.setValue("geometry", self.geometry())
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                self.tr("Desktop Icon Manager"),
                self.tr(
                    "Application minimized to tray. Click or double-click to restore."
                ),
                QSystemTrayIcon.MessageIcon.Information,
                Config.TRAY_NOTIFICATION_DURATION,
            )
            return

        self._run_final_cleanup()
        event.accept()

        # Hide tray icon to avoid ghost icon in taskbar
        if self.tray_icon:
            self.tray_icon.hide()

        if is_pyinstaller:
            try:
                hwnd_console = win32gui.GetConsoleWindow()
                if hwnd_console:
                    win32gui.PostMessage(hwnd_console, win32con.WM_CLOSE, 0, 0)
            except Exception:
                pass
        QApplication.quit()

    def _silent_update_check(self):
        from ui.update_dialog import UpdateCheckWorker

        self._update_worker = UpdateCheckWorker(self)
        self._update_worker.finished.connect(self._on_silent_update_result)
        self._update_worker.error.connect(lambda _: None)
        self._update_worker.start()

    def _on_silent_update_result(self, remote: str):
        try:
            current = tuple(int(x) for x in Config.VERSION.split("."))
            latest = tuple(int(x) for x in remote.split("."))
        except ValueError:
            return
        if latest > current:
            self.tray_icon.showMessage(
                "Desktop Icon Backup Manager",
                self.tr("A new version is available! (%1)").replace("%1", remote),
                QSystemTrayIcon.MessageIcon.Information,
                8000,
            )
            self.log(
                self.tr("\U0001f514 A new version is available: %1 (current: %2)")
                .replace("%1", remote)
                .replace("%2", Config.VERSION)
            )

    def show_update_dialog(self):
        dlg = UpdateDialog(self)
        dlg.exec()

    def show_stats_dialog(self):
        from ui.stats_dialog import StatsDialog

        dlg = StatsDialog(self.settings, self)
        dlg.exec()

    def show_shortcuts_dialog(self):
        dialogs.show_shortcuts_dialog(self)

    def toggle_icon_visibility(self):
        """Toggle the visibility of desktop icons"""
        self.log(self.tr("Updating desktop icon visibility..."))
        success = self.visibility_manager.toggle_icon_visibility(self.log)
        if success:
            self.log(self.tr("Desktop icon visibility updated."))
            self._restart_autohide_if_icons_visible()
        else:
            self.log(self.tr("✗ Failed to show/hide desktop icons."))

    def show_desktop_icons(self):
        """Show desktop icons"""
        self.log(self.tr("Attempting to show desktop icons..."))
        success = self.visibility_manager.show_icons(self.log)
        if success:
            self.log(self.tr("Desktop icons are now visible."))
            self._restart_autohide_if_icons_visible()
        else:
            self.log(self.tr("✗ Failed to show desktop icons."))

    def hide_desktop_icons(self):
        """Hide desktop icons"""
        self.log(self.tr("Attempting to hide desktop icons..."))
        success = self.visibility_manager.hide_icons(self.log)
        if success:
            self.log(self.tr("Desktop icons are now hidden."))
            self._stop_autohide_timer()
        else:
            self.log(self.tr("✗ Failed to hide desktop icons."))
