"""Backup Manager Dialog for managing backup files"""

import os
import json

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QPushButton,
    QMessageBox,
    QMenu,
    QTextEdit,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QColor, QFont

from core.config import Config
from core.comparator import BackupComparator
from utils.helpers import parse_backup_filename, parse_resolution_string
from ui.preview_widget import IconPreviewWidget, DiffPreviewWidget, make_legend_widget


class BackupManagerWindow(QDialog):
    restore_requested = pyqtSignal(str)
    list_changed_signal = pyqtSignal()

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle(self.tr("Select, Restore, or Delete Backup"))
        # Bug 6 fix: use setMinimumSize instead of setFixedSize so it
        # adapts to high-DPI / small screens.
        self.setMinimumSize(1200, 600)
        self.resize(1600, 800)

        root = QVBoxLayout(self)
        root.setSpacing(8)

        root.addWidget(
            QLabel(self.tr("Select a backup to restore or right-click for options."))
        )

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.tr("Search by tag, resolution, or date...")
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_backups)
        root.addWidget(self.search_input)

        # ── Main horizontal split ────────────────────────────────────────────
        h_split = QHBoxLayout()

        # Left: table of backups
        left = QVBoxLayout()

        # Improvement: QTableWidget instead of fragile monospaced text
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                self.tr("Tag / Description"),
                self.tr("Resolution"),
                self.tr("Icons"),
                self.tr("Timestamp"),
            ]
        )
        # Col 0: Tag/Description — stretches to fill remaining space
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        # Col 1: Resolution — fixed, enough for "1920x1080"
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().resizeSection(1, 80)
        # Col 2: Icons — fixed, enough for a 3-digit count
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().resizeSection(2, 46)
        # Col 3: Timestamp — fixed, enough for "2026/02/22 16:30:02"
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().resizeSection(3, 140)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("font-family: 'Segoe UI'; font-size: 11px;")
        self.table.setSortingEnabled(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setMinimumWidth(490)
        # Centre-align headers for numeric/date columns
        for col in (1, 2, 3):
            self.table.horizontalHeaderItem(col).setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
        left.addWidget(self.table)
        h_split.addLayout(left, 4)

        # Right: preview + info
        right = QVBoxLayout()
        right.setSpacing(8)

        # Live diff preview label — styled to stand out
        preview_label = QLabel(self.tr("Layout Preview (saved positions vs current):"))
        preview_label.setStyleSheet(
            "font-family: 'Segoe UI'; font-size: 10px;"
            " font-weight: bold; background: transparent; padding: 0px;"
        )
        right.addWidget(preview_label)

        self.preview_widget = DiffPreviewWidget()
        right.addWidget(self.preview_widget, stretch=1)

        self.info_label = QLabel(self.tr("Select a backup to see details."))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            "border: 1px solid palette(mid); border-radius: 4px;"
            " padding: 10px; font-family: 'Segoe UI'; font-size: 12px;"
        )
        self.info_label.setMinimumHeight(100)

        # Legend sits to the right of info_label, same height
        self._legend_widget = make_legend_widget()
        self._legend_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self._legend_widget.setMinimumWidth(420)

        info_row = QHBoxLayout()
        info_row.setSpacing(8)
        info_row.addWidget(self.info_label, stretch=1)
        info_row.addWidget(self._legend_widget)
        right.addLayout(info_row)
        h_split.addLayout(right, 8)

        root.addLayout(h_split)

        # Bottom buttons
        btn_row = QHBoxLayout()
        self.btn_restore = QPushButton(self.tr("Restore Selected Layout"))
        self.btn_restore.clicked.connect(self.restore_selected)
        self.btn_restore.setEnabled(False)

        self.btn_compare = QPushButton(self.tr("📊 Compare Two Selected..."))
        self.btn_compare.clicked.connect(self.compare_selected_pair)
        self.btn_compare.setEnabled(False)

        self.btn_close = QPushButton(self.tr("Close"))
        self.btn_close.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_restore)
        btn_row.addWidget(self.btn_compare)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_close)
        root.addLayout(btn_row)

        # Connect signals
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.restore_selected)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self.load_backups()

    # ── Data loading ─────────────────────────────────────────────────────────

    def load_backups(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        backups = self.manager.get_all_backup_filenames()

        for filename in backups:
            readable_date, resolution, _ = parse_backup_filename(filename)
            description = ""
            icon_count = self.tr("N/A")
            filepath = os.path.join(Config.BACKUP_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    description = data.get("description", "").strip()
                    icon_count = data.get("icon_count", self.tr("N/A"))
            except (OSError, json.JSONDecodeError):
                pass

            row = self.table.rowCount()
            self.table.insertRow(row)

            desc_item = QTableWidgetItem(description)
            desc_item.setData(Qt.ItemDataRole.UserRole, filename)
            self.table.setItem(row, 0, desc_item)

            res_item = QTableWidgetItem(resolution)
            res_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, res_item)

            count_item = QTableWidgetItem(str(icon_count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, count_item)

            date_item = QTableWidgetItem(readable_date)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, date_item)

        self.table.setSortingEnabled(True)

        if not backups:
            self.table.setRowCount(1)
            no_item = QTableWidgetItem(self.tr("No backups found."))
            no_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.table.setItem(0, 0, no_item)

    def _selected_filename(self) -> str | None:
        rows = self.table.selectedItems()
        if not rows:
            return None
        filename = self.table.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        return filename

    # ── Selection / preview ──────────────────────────────────────────────────

    def on_selection_changed(self):
        filename = self._selected_filename()
        if not filename:
            self.preview_widget.update_preview({}, {}, (1920, 1080))
            self.info_label.setText(self.tr("Select a backup to see details."))
            self.btn_restore.setEnabled(False)
            self.btn_compare.setEnabled(False)
            return

        filepath = os.path.join(Config.BACKUP_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved_icons = data.get("icons", {})
            res_str = parse_backup_filename(filename)[1]
            res_tuple = parse_resolution_string(res_str) or (1920, 1080)

            # Fetch live positions for the diff preview
            try:
                current_icons = self.manager.get_current_icon_positions()
            except Exception:
                current_icons = {}

            self.preview_widget.update_preview(saved_icons, current_icons, res_tuple)

            desc = data.get("description", self.tr("None"))
            ts_raw = data.get("timestamp", self.tr("N/A"))
            try:
                from datetime import datetime as _dt

                ts = _dt.fromisoformat(ts_raw).strftime("%Y/%m/%d %H:%M:%S")
            except Exception:
                ts = ts_raw
            count = len(saved_icons)
            info = (
                f"<b>{self.tr('File')}:</b> {filename}<br>"
                f"<b>{self.tr('Icons')}:</b> {count}<br>"
                f"<b>{self.tr('Resolution')}:</b> {res_str}<br>"
                f"<b>{self.tr('Description')}:</b> {desc}<br>"
                f"<b>{self.tr('Timestamp')}:</b> {ts}"
            )
            self.info_label.setText(info)
            self.btn_restore.setEnabled(True)
            self.btn_compare.setEnabled(True)
        except (OSError, json.JSONDecodeError) as e:
            self.info_label.setText(f"{self.tr('Error')}: {str(e)}")
            self.btn_restore.setEnabled(False)
            self.btn_compare.setEnabled(False)

    def filter_backups(self, query: str):
        query = query.lower()
        for row in range(self.table.rowCount()):
            row_text = " ".join(
                self.table.item(row, col).text()
                for col in range(self.table.columnCount())
                if self.table.item(row, col)
            ).lower()
            self.table.setRowHidden(row, query not in row_text)

    # ── Context menu ─────────────────────────────────────────────────────────

    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        filename = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not filename:
            return

        menu = QMenu(self)
        restore_action = QAction(self.tr("🔄 Restore Selected"), self)
        restore_action.triggered.connect(self.restore_selected)

        delete_action = QAction(self.tr("🗑️ Delete Selected"), self)
        delete_action.triggered.connect(self.delete_selected)

        # Improvement: compare any two backups (not just vs latest)
        compare_latest_action = QAction(self.tr("📊 Compare with Latest"), self)
        compare_latest_action.triggered.connect(self.compare_with_latest)

        menu.addAction(restore_action)
        menu.addAction(compare_latest_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.table.mapToGlobal(pos))

    # ── Actions ──────────────────────────────────────────────────────────────

    def restore_selected(self):
        fn = self._selected_filename()
        if not fn:
            return

        filepath = os.path.join(Config.BACKUP_DIR, fn)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            readable_date, resolution, _ = parse_backup_filename(fn)
            description = data.get("description", self.tr("N/A"))
            icon_count = data.get("icon_count", self.tr("N/A"))

            reply = QMessageBox.question(
                self,
                self.tr("Confirm Restore"),
                self.tr(
                    "Restore icon positions from the selected backup file:\n\n"
                    "File: %1\n"
                    "Resolution: %2\n"
                    "Icons: %3\n"
                    "Tag: %4\n"
                    "Timestamp: %5\n\n"
                    "Are you sure you want to proceed?"
                )
                .replace("%1", fn)
                .replace("%2", resolution)
                .replace("%3", str(icon_count))
                .replace("%4", description)
                .replace("%5", readable_date),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.restore_requested.emit(fn)
                self.accept()

        except (OSError, json.JSONDecodeError) as e:
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Failed to load backup file:\n%1").replace("%1", str(e)),
            )

    def delete_selected(self):
        fn = self._selected_filename()
        if not fn:
            return

        reply = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Are you sure you want to delete this backup?\n\n%1").replace(
                "%1", fn
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.delete_backup(fn):
                self.load_backups()
                self.list_changed_signal.emit()
                QMessageBox.information(
                    self, self.tr("Success"), self.tr("Backup deleted successfully.")
                )
            else:
                QMessageBox.critical(
                    self, self.tr("Error"), self.tr("Failed to delete backup file.")
                )

    def compare_with_latest(self):
        """Compare selected backup against the latest one."""
        selected = self._selected_filename()
        if not selected:
            QMessageBox.warning(
                self,
                self.tr("No Selection"),
                self.tr("Please select a backup to compare."),
            )
            return

        latest = self.manager.get_latest_backup_filename()
        if not latest:
            QMessageBox.warning(
                self, self.tr("Error"), self.tr("No latest backup found")
            )
            return

        if selected == latest:
            QMessageBox.information(
                self,
                self.tr("Same Backup"),
                self.tr("You selected the latest backup. Nothing to compare."),
            )
            return

        self._show_comparison_dialog(selected, latest, is_latest=True)

    def compare_selected_pair(self):
        """
        Improvement: compare any two backups. Opens a mini-picker dialog so
        the user can choose the second file without being limited to 'latest'.
        """
        selected = self._selected_filename()
        if not selected:
            QMessageBox.warning(
                self,
                self.tr("No Selection"),
                self.tr("Please select a backup first."),
            )
            return

        all_files = self.manager.get_all_backup_filenames()
        other_files = [f for f in all_files if f != selected]
        if not other_files:
            QMessageBox.information(
                self,
                self.tr("Not Enough Backups"),
                self.tr("There is only one backup. Nothing to compare against."),
            )
            return

        picker = _BackupPickerDialog(other_files, self)
        if picker.exec() == QDialog.DialogCode.Accepted and picker.chosen:
            self._show_comparison_dialog(selected, picker.chosen, is_latest=False)

    def _show_comparison_dialog(self, file_a: str, file_b: str, is_latest: bool):
        path_a = os.path.join(Config.BACKUP_DIR, file_a)
        path_b = os.path.join(Config.BACKUP_DIR, file_b)
        report = BackupComparator.compare(path_a, path_b)

        if not report:
            QMessageBox.critical(
                self, self.tr("Error"), self.tr("Failed to compare backups")
            )
            return

        label_b = f"{file_b} ({self.tr('latest')})" if is_latest else file_b

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Comparison Results"))
        dialog.resize(650, 550)
        dialog.setStyleSheet("""
            QLabel { border: 1px solid palette(mid);
                     border-radius: 4px; padding: 12px; font-family: 'Segoe UI'; font-size: 11px; }
            QTextEdit { border: 1px solid palette(mid);
                        border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; }
            QPushButton { color: #ffffff; background-color: #0078D7; border: none;
                          border-radius: 4px; padding: 8px 16px; font-family: 'Segoe UI';
                          font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #106EBE; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel(
            f"<b style='color: #007a6a;'>{self.tr('Comparing Backups:')}</b><br>"
            f"<span style='color: #0066cc;'>📄 {file_a}</span><br>"
            f"<span style='color: #0055aa;'>📄 {label_b}</span>"
        )
        layout.addWidget(header)

        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setHtml(self._colorize_report(report))
        layout.addWidget(text_area)

        btn_close = QPushButton(self.tr("✓ Close"))
        btn_close.clicked.connect(dialog.accept)
        btn_close.setMinimumHeight(35)
        layout.addWidget(btn_close)

        dialog.exec()

    def _colorize_report(self, report: str) -> str:
        lines = report.split("\n")
        html_lines = []
        for line in lines:
            if line.startswith("==="):
                html_lines.append(
                    f"<p style='color:#007a6a;font-weight:bold;font-size:12pt;'>{line}</p>"
                )
            elif line.startswith("---"):
                html_lines.append(
                    f"<p style='color:#856a00;font-weight:bold;margin-top:10px;'>{line}</p>"
                )
            elif "Icon(s) Added:" in line or "  + " in line:
                html_lines.append(f"<p style='color:#007a6a;'>{line}</p>")
            elif "Icon(s) Removed:" in line or "  - " in line:
                html_lines.append(f"<p style='color:#cc2200;'>{line}</p>")
            elif "Icon(s) Moved:" in line or "  ↔" in line:
                html_lines.append(f"<p style='color:#856a00;'>{line}</p>")
            elif "Icon(s) Unchanged:" in line:
                html_lines.append(f"<p style='color:gray;'>{line}</p>")
            elif "✓" in line:
                html_lines.append(
                    f"<p style='color:#2e7d32;font-weight:bold;'>{line}</p>"
                )
            else:
                html_lines.append(f"<p style=''>{line}</p>")
        return "".join(html_lines)


class _BackupPickerDialog(QDialog):
    """Small helper dialog to pick a second backup file for comparison."""

    def __init__(self, filenames: list[str], parent=None):
        super().__init__(parent)
        self.chosen: str | None = None
        self.setWindowTitle(self.tr("Pick Backup to Compare Against"))
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Select the second backup file:")))

        from PyQt6.QtWidgets import QListWidget, QListWidgetItem

        self.list = QListWidget()
        for fn in filenames:
            readable_date, resolution, _ = parse_backup_filename(fn)
            item = QListWidgetItem(f"{readable_date}  [{resolution}]  {fn}")
            item.setData(Qt.ItemDataRole.UserRole, fn)
            self.list.addItem(item)
        self.list.itemDoubleClicked.connect(self._accept)
        layout.addWidget(self.list)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton(self.tr("Compare"))
        ok_btn.clicked.connect(self._accept)
        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _accept(self):
        sel = self.list.selectedItems()
        if sel:
            self.chosen = sel[0].data(Qt.ItemDataRole.UserRole)
            self.accept()
