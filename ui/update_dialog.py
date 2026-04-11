"""Update Checker Dialog for Desktop Icon Backup Manager"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices

from core.config import Config

# ── Background worker ─────────────────────────────────────────────────────────


class UpdateCheckWorker(QThread):
    """Fetches the remote version.txt in a background thread."""

    finished = pyqtSignal(str)  # emits remote version string on success
    error = pyqtSignal(str)  # emits error message on failure

    VERSION_URL = (
        "https://raw.githubusercontent.com/mapi68/"
        "desktop-icon-backup-manager/master/version.txt"
    )

    def run(self):
        try:
            import urllib.request

            with urllib.request.urlopen(self.VERSION_URL, timeout=10) as resp:
                remote = resp.read().decode("utf-8").strip()
            self.finished.emit(remote)
        except Exception as exc:
            self.error.emit(str(exc))


# ── Dialog ────────────────────────────────────────────────────────────────────


class UpdateDialog(QDialog):
    """Shows current version and checks for updates online."""

    RELEASES_URL = (
        "https://github.com/mapi68/desktop-icon-backup-manager/releases/latest"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Check for Updates"))
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        # Config.VERSION is always available: loaded from the bundled
        # version.txt both in Python source mode and in the PyInstaller
        # .exe (compile.spec includes 'version.txt' in datas).
        self._local_version = Config.VERSION

        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 28, 28, 24)

        # ── Current version row ───────────────────────────────────────────────
        current_row = QHBoxLayout()
        current_row.addWidget(QLabel(f"<b>{self.tr('Installed version:')}</b>"))
        self.lbl_current = QLabel(self._local_version)
        current_row.addWidget(self.lbl_current)
        current_row.addStretch()
        layout.addLayout(current_row)

        # ── Latest version row ────────────────────────────────────────────────
        latest_row = QHBoxLayout()
        latest_row.addWidget(QLabel(f"<b>{self.tr('Latest version:')}</b>"))
        self.lbl_latest = QLabel(self.tr("Checking..."))
        latest_row.addWidget(self.lbl_latest)
        latest_row.addStretch()
        layout.addLayout(latest_row)

        # ── Progress bar (visible while checking) ─────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # ── Status label ──────────────────────────────────────────────────────
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_download = QPushButton(self.tr("Download Update"))
        self.btn_download.setVisible(False)
        self.btn_download.clicked.connect(self._open_releases)
        btn_row.addWidget(self.btn_download)

        self.btn_recheck = QPushButton(self.tr("Check Again"))
        self.btn_recheck.clicked.connect(self._start_check)
        btn_row.addWidget(self.btn_recheck)

        btn_close = QPushButton(self.tr("Close"))
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

        self._apply_style()
        self._start_check()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _apply_style(self):
        # Styles are loaded from styles/theme.qss at application level.
        # UpdateDialog is matched by class name in the QSS.
        pass

    def _start_check(self):
        self.lbl_latest.setText(self.tr("Checking..."))
        self.lbl_status.setText("")
        self.progress.setVisible(True)
        self.btn_download.setVisible(False)
        self.btn_recheck.setEnabled(False)

        self.worker = UpdateCheckWorker(self)
        self.worker.finished.connect(self._on_success)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_success(self, remote: str):
        self.progress.setVisible(False)
        self.btn_recheck.setEnabled(True)
        self.lbl_latest.setText(remote)

        try:
            current = tuple(int(x) for x in self._local_version.split("."))
            latest = tuple(int(x) for x in remote.split("."))
        except ValueError:
            self.lbl_status.setText(
                f"<span style='color:#e57373;'>"
                f"✗ {self.tr('Could not parse version numbers.')}</span>"
            )
            return

        if latest > current:
            self.lbl_status.setText(
                f"<span style='color:#4CAF50; font-weight:bold;'>"
                f"🔔 {self.tr('A new version is available!')}</span>"
            )
            self.btn_download.setVisible(True)
        elif latest == current:
            self.lbl_status.setText(
                f"<span style='color:#4CAF50;'>"
                f"✔ {self.tr('You are using the latest version.')}</span>"
            )
        else:
            self.lbl_status.setText(
                f"<span style='color:#aaa;'>"
                f"{self.tr('You are using a pre-release version.')}</span>"
            )

    def _on_error(self, message: str):
        self.progress.setVisible(False)
        self.btn_recheck.setEnabled(True)
        self.lbl_latest.setText(self.tr("Unknown"))
        self.lbl_status.setText(
            f"<span style='color:#e57373;'>"
            f"✗ {self.tr('Could not check for updates:')}<br>{message}</span>"
        )

    def _open_releases(self):
        QDesktopServices.openUrl(QUrl(self.RELEASES_URL))
