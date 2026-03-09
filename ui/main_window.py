"""Main Window for Desktop Icon Backup Manager"""

from datetime import datetime
import os
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import os
import json


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
)

from PyQt6.QtCore import (
    QSettings,
    QTranslator,
    QLocale,
    QCoreApplication,
    QRect,
    QTimer,
    QUrl,
)
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QDesktopServices, QCursor

import win32gui
import win32con

from core.config import Config, resource_path
from core.icon_manager import DesktopIconManager
from utils.threads import IconWorker
from utils.helpers import (
    get_display_metadata,
    get_readable_date,
    get_resolution_from_filename,
)
from ui.backup_dialog import BackupManagerWindow, _ask
from ui.update_dialog import UpdateDialog
from ui.preview_widget import DiffPreviewWidget, make_legend_widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = DesktopIconManager()
        self.current_resolution = get_display_metadata().get(
            "primary_resolution", self.tr("Unknown")
        )

        app_path = Path(os.path.abspath(sys.argv[0])).parent
        settings_file_path = app_path / "settings.ini"
        self.settings = QSettings(str(settings_file_path), QSettings.Format.IniFormat)

        self.worker = None
        self.tray_icon = None

        self.create_tray_icon()

        self.DEFAULT_GEOMETRY = QRect(100, 100, 800, 650)

        self.setup_ui()
        self.setup_shortcuts()
        self.load_settings()

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
        self.close()

    def setup_ui(self):
        self.setWindowTitle(self.tr("Desktop Icon Backup Manager by mapi68"))
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

        self.action_remove_all = QAction(self.tr("Remove All Backups..."), self)
        self.action_remove_all.triggered.connect(self.confirm_and_delete_all_backups)
        file_menu.addAction(self.action_remove_all)

        file_menu.addSeparator()
        action_exit = QAction(self.tr("E&xit"), self)
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.exit_application)
        file_menu.addAction(action_exit)

        settings_menu = menu_bar.addMenu(self.tr("&Settings"))

        action_open_settings = QAction(self.tr("Open Settings Menu"), self)
        action_open_settings.setShortcut(QKeySequence("Ctrl+,"))
        action_open_settings.triggered.connect(self.show_settings_menu)

        self.action_start_minimized = QAction(
            self.tr("Start Minimized to Tray"), self, checkable=True
        )
        self.action_start_minimized.triggered.connect(
            lambda checked: self.settings.setValue("start_minimized", checked)
        )
        settings_menu.addAction(self.action_start_minimized)

        settings_menu.addSeparator()

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

        self.action_adaptive_scaling = QAction(
            self.tr("Enable Adaptive Scaling on Restore"), self, checkable=True
        )
        self.action_adaptive_scaling.triggered.connect(
            lambda checked: self.settings.setValue("adaptive_scaling_enabled", checked)
        )
        settings_menu.addAction(self.action_adaptive_scaling)

        settings_menu.addSeparator()

        self.action_close_to_tray = QAction(
            self.tr("Minimize to Tray on Close ('X' button)"), self, checkable=True
        )
        self.action_close_to_tray.triggered.connect(
            lambda checked: self.settings.setValue("close_to_tray", checked)
        )
        settings_menu.addAction(self.action_close_to_tray)

        settings_menu.addSeparator()

        self.cleanup_group = QMenu(self.tr("Automatic Backup Cleanup Limit"), self)
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

        help_menu = menu_bar.addMenu(self.tr("&Help"))

        action_manual = QAction(self.tr("Online User Manual"), self)
        action_manual.setShortcut(QKeySequence("F1"))
        action_manual.triggered.connect(self.open_online_manual)
        help_menu.addAction(action_manual)

        help_menu.addSeparator()

        action_shortcuts = QAction(self.tr("Keyboard Shortcuts"), self)
        action_shortcuts.triggered.connect(self.show_shortcuts_dialog)
        help_menu.addAction(action_shortcuts)

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

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.save_tag_input = QLineEdit()
        self.save_tag_input.setPlaceholderText(
            self.tr("Optional: Enter a descriptive tag/description...")
        )

        tag_input_row = QHBoxLayout()
        tag_input_row.addWidget(QLabel(self.tr("Save Tag:")))
        tag_input_row.addWidget(self.save_tag_input, 1)
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

        self.btn_restore_select = QPushButton(self.tr("↺ BACKUP MANAGER"))
        self.btn_restore_select.setMinimumHeight(50)

        self.btn_restore_select.setToolTip(
            self.tr(
                "Opens a window to select a specific backup file to restore or delete.\n\nShortcut: Ctrl+M"
            )
        )

        self.btn_restore_select.clicked.connect(self.open_backup_manager)
        self.btn_restore_select.setObjectName("backupManagerButton")

        action_buttons_row.addWidget(self.btn_save_latest, 1)
        action_buttons_row.addWidget(self.btn_restore_latest, 1)
        action_buttons_row.addWidget(self.btn_restore_select, 1)

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
        self.btn_clear_log.clicked.connect(self.log_area.clear)
        self.btn_clear_log.setMaximumWidth(150)
        self.btn_clear_log.setObjectName("clearLogButton")
        log_button_layout.addWidget(self.btn_clear_log)

        layout.addLayout(log_button_layout)

        self.setStyleSheet("""
            QPushButton[objectName="saveButton"],
            QPushButton[objectName="restoreButton"],
            QPushButton[objectName="backupManagerButton"],
            QPushButton[objectName="clearLogButton"]
            { color: white; font-weight: bold; border-radius: 6px; padding: 8px; font-size: 13px; }
            QPushButton[objectName="saveButton"]:hover,
            QPushButton[objectName="restoreButton"]:hover,
            QPushButton[objectName="backupManagerButton"]:hover,
            QPushButton[objectName="clearLogButton"]:hover
            { opacity: 0.8; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
            QPushButton#saveButton { background-color: #00A65A; }
            QPushButton#backupManagerButton { background-color: #0078D7; }
            QPushButton#restoreButton { background-color: #CC0000; }
            QPushButton#clearLogButton { background-color: #6c757d; }
            QTextEdit { border: 1px solid #ddd; border-radius: 4px; padding: 5px; font-family: 'Consolas', monospace; font-size: 11px; }
            QProgressBar { border: 1px solid #ddd; border-radius: 4px; text-align: center; height: 20px; }
            QProgressBar::chunk { background-color: #0078D7; border-radius: 3px; }
        """)

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

        manager_shortcut = QAction(self.tr("Backup Manager"), self)
        manager_shortcut.setShortcut(QKeySequence("Ctrl+M"))
        manager_shortcut.triggered.connect(self.open_backup_manager)
        self.addAction(manager_shortcut)

        settings_shortcut = QAction(self.tr("Settings"), self)
        settings_shortcut.setShortcut(QKeySequence("Ctrl+,"))
        settings_shortcut.triggered.connect(self.show_settings_menu)
        self.addAction(settings_shortcut)

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

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")

        if not self.isVisible() and ("✗" in message or "CRITICAL ERROR" in message):
            self.tray_icon.showMessage(
                self.tr("Desktop Icon Manager"),
                message,
                QSystemTrayIcon.MessageIcon.Warning,
                5000,
            )

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

    def quick_save_with_tag(self):
        tag = self.save_tag_input.text().strip()
        description = tag if tag else self.tr("Quick Backup")
        self.start_save(description=description)

    def start_restore_specific(self, filename: str):
        self._start_restore(filename)

    def show_about_dialog(self):
        html = (
            f"<h2>Desktop Icon Backup Manager</h2>"
            f"<p>{self.tr('A simple yet powerful tool to save and restore Windows desktop icon positions.')}</p>"
            f"<h3>{self.tr('Key Features:')}</h3>"
            f"<ul>"
            f"<li><b>{self.tr('Quick Save:')}</b> {self.tr('Save icons with an optional descriptive tag.')}</li>"
            f"<li><b>{self.tr('Backup Management:')}</b> {self.tr('Select, restore, or delete specific backups.')}</li>"
            f"<li><b>{self.tr('Live Diff Preview:')}</b> {self.tr('See which icons will move before restoring.')}</li>"
            f"<li><b>{self.tr('Visual Preview:')}</b> {self.tr('See a mini-map of your layout.')}</li>"
            f"<li><b>{self.tr('Backup Comparison:')}</b> {self.tr('Compare any two backups to see added, removed, and moved icons.')}</li>"
            f"<li><b>{self.tr('Adaptive Scaling:')}</b> {self.tr('Automatic adjustment for different resolutions.')}</li>"
            f"<li><b>{self.tr('Automatic Cleanup:')}</b> {self.tr('Set a limit on backups to keep.')}</li>"
            f"<li><b>{self.tr('Random Scramble:')}</b> {self.tr('Randomize icon positions after backup.')}</li>"
            f"<li><b>{self.tr('Tray Integration:')}</b> {self.tr('Quick access via tray.')}</li>"
            f"</ul>"
            f"<p><b>{self.tr('Version:')}</b> {Config.VERSION}<br>"
            f"<b>{self.tr('Development:')}</b> mapi68<br></p>"
            f"<p><a href='https://ko-fi.com/mapi68'>{self.tr('Support this project on Ko-fi')}</a></p>"
        )
        QMessageBox.about(self, self.tr("About Desktop Icon Backup Manager"), html)

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
                "Are you absolutely sure you want to permanently delete ALL %n desktop icon backup file(s)?\n\nThis action cannot be undone!",
                None,
                backup_count,
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
        from utils.helpers import parse_resolution_string

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
        from PyQt6.QtWidgets import QSizePolicy as QSP

        legend.setSizePolicy(QSP.Policy.Preferred, QSP.Policy.Expanding)
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
        mode = self.worker.mode if self.worker else "unknown"

        if mode == "restore" and success:
            self._check_display_metadata(saved_metadata)

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
        else:
            self.statusBar().showMessage(self.tr("Operation failed"), 3000)
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Operation failed (%1). Check the log for details.").replace(
                    "%1", str(mode.capitalize())
                ),
            )

        self.worker = None

    def _check_display_metadata(self, saved_metadata: Dict):
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
            if self.isVisible():
                self.log(
                    self.tr("Auto-Save on Exit enabled. Performing silent backup...")
                )
            cleanup_limit = self.settings.value("cleanup_limit", 0, type=int)
            self.manager.save(
                lambda msg: print(f"{self.tr('Auto-Save Log')}: {msg}"),
                description=self.tr("Auto-Save on Exit"),
                max_backup_count=cleanup_limit,
            )

    def closeEvent(self, event):
        close_to_tray = self.action_close_to_tray.isChecked()
        is_pyinstaller = getattr(sys, "frozen", False)

        if close_to_tray and self.isVisible():
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
        from core.config import Config

        try:
            current = tuple(int(x) for x in Config.VERSION.split("."))
            latest = tuple(int(x) for x in remote.split("."))
        except ValueError:
            return
        if latest > current:
            self.tray_icon.showMessage(
                self.tr("Desktop Icon Backup Manager"),
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

    def show_shortcuts_dialog(self):
        shortcuts_text = f"""
        <h2>{self.tr("Keyboard Shortcuts")}</h2>
        <table style='width:100%; border-collapse: collapse;'>
            <tr style='background-color: #2b2b2b;'>
                <th style='padding: 8px; text-align: left; border: 1px solid #444;'>{self.tr("Shortcut")}</th>
                <th style='padding: 8px; text-align: left; border: 1px solid #444;'>{self.tr("Action")}</th>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #444;'><b>Ctrl+S</b></td>
                <td style='padding: 8px; border: 1px solid #444;'>{self.tr("Quick Save current layout")}</td>
            </tr>
            <tr style='background-color: #1e1e1e;'>
                <td style='padding: 8px; border: 1px solid #444;'><b>Ctrl+M</b></td>
                <td style='padding: 8px; border: 1px solid #444;'>{self.tr("Open Backup Manager")}</td>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #444;'><b>Ctrl+,</b></td>
                <td style='padding: 8px; border: 1px solid #444;'>{self.tr("Open Settings menu")}</td>
            </tr>
            <tr style='background-color: #1e1e1e;'>
                <td style='padding: 8px; border: 1px solid #444;'><b>F1</b></td>
                <td style='padding: 8px; border: 1px solid #444;'>{self.tr("Open Online User Manual")}</td>
            </tr>
            <tr>
                <td style='padding: 8px; border: 1px solid #444;'><b>Ctrl+Q</b></td>
                <td style='padding: 8px; border: 1px solid #444;'>{self.tr("Exit Application")}</td>
            </tr>
        </table>
        <br>
        <p style='color: {Config.COLOR_TEXT_DIM}; font-size: 11px;'>{self.tr("Tip: Hover over buttons to see additional shortcuts in tooltips.")}</p>
        """

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Keyboard Shortcuts"))
        dialog.setMinimumWidth(Config.SHORTCUTS_DIALOG_MIN_WIDTH)
        dialog.setMinimumHeight(Config.SHORTCUTS_DIALOG_MIN_HEIGHT)

        layout = QVBoxLayout(dialog)

        text_browser = QTextEdit()
        text_browser.setReadOnly(True)
        text_browser.setHtml(shortcuts_text)
        layout.addWidget(text_browser)

        btn_close = QPushButton(self.tr("Close"))
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)

        dialog.exec()
