"""Structured logging for Desktop Icon Backup Manager.

Provides a single ``logging.Logger`` named ``"dibm"`` that routes
messages to three destinations:

1. **Rotating file** — ``history.log`` next to the executable, capped at
   500 lines (~50 KB) with one backup file.
2. **GUI handler** — forwards messages to a ``QTextEdit`` widget via a
   Qt signal (thread-safe).  Must be installed explicitly after the main
   window is created by calling ``attach_gui_handler(text_edit)``.
3. **stderr** — standard ``StreamHandler`` for console / CLI mode.

All core modules (icon_manager, desktop_visibility, comparator, threads)
should use::

    import logging
    logger = logging.getLogger("dibm")
    logger.info("…")

The GUI ``MainWindow.log()`` method now delegates to ``logger.info()``,
which automatically fans out to file + widget + console.
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

# ── Logger singleton ──────────────────────────────────────────────────────────
_LOG_NAME = "dibm"
_LOG_FORMAT = "[%(asctime)s] %(message)s"
_LOG_DATE_FMT = "%Y-%m-%d %H:%M:%S"
_LOG_DATE_FMT_SHORT = "%H:%M:%S"


def get_logger() -> logging.Logger:
    """Return the application-wide logger (creates it on first call)."""
    return logging.getLogger(_LOG_NAME)


# ── File handler (rotating) ──────────────────────────────────────────────────


def setup_file_handler(log_path: Path) -> logging.FileHandler:
    """
    Attach a RotatingFileHandler to the ``dibm`` logger.

    The handler keeps a single file of up to ~50 KB (roughly 500 lines)
    with one backup file (``.log.1``).  This replaces the manual
    ``_trim_log_file()`` approach.
    """
    logger = get_logger()
    handler = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=50_000,
        backupCount=1,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return handler


# ── Console handler (stderr) ─────────────────────────────────────────────────


def setup_console_handler() -> logging.StreamHandler:
    """Attach a StreamHandler for CLI / silent mode output."""
    logger = get_logger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return handler


# ── GUI handler (QTextEdit via signal) ────────────────────────────────────────


class _QtSignalBridge(QObject):
    """Thread-safe bridge: emit a Qt signal from any thread."""

    message = pyqtSignal(str)


class QtTextEditHandler(logging.Handler):
    """
    Logging handler that appends formatted messages to a ``QTextEdit``.

    Uses a Qt signal internally so it is safe to call ``logger.info()``
    from worker threads — the actual ``append()`` happens in the GUI
    thread via signal/slot.
    """

    def __init__(self, text_edit):
        super().__init__()
        self._bridge = _QtSignalBridge()
        self._bridge.message.connect(text_edit.append)
        self.setFormatter(
            logging.Formatter("[%(asctime)s] %(message)s", datefmt=_LOG_DATE_FMT_SHORT)
        )

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self._bridge.message.emit(msg)
        except RuntimeError:
            # Widget may have been destroyed during shutdown
            pass


def attach_gui_handler(text_edit) -> QtTextEditHandler:
    """
    Install a handler that writes to *text_edit* (``QTextEdit``).

    Call this once from ``MainWindow.__init__`` after the log area is
    created.  Returns the handler so it can be removed later if needed.
    """
    logger = get_logger()
    handler = QtTextEditHandler(text_edit)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return handler


# ── Bootstrap ────────────────────────────────────────────────────────────────


def init_logging(log_path: Path, *, console: bool = False) -> None:
    """
    One-time setup: set the logger level and attach file handler.

    Parameters
    ----------
    log_path : Path
        Full path to ``history.log``.
    console : bool
        If ``True``, also attach a stderr handler (useful for CLI mode).
    """
    logger = get_logger()
    logger.setLevel(logging.DEBUG)
    # Prevent duplicate handlers on repeated calls
    if not logger.handlers:
        setup_file_handler(log_path)
        if console:
            setup_console_handler()


def clear_log_file(log_path: Path) -> None:
    """Clear the log file and its backup (called from GUI 'Clear Log').

    Instead of deleting the file (which would leave the RotatingFileHandler
    with a stale file descriptor), we close the handler, truncate the file,
    then reopen the handler so logging continues normally.
    """
    logger = get_logger()

    # Find and close the RotatingFileHandler
    file_handler: Optional[logging.handlers.RotatingFileHandler] = None
    for h in logger.handlers:
        if isinstance(h, logging.handlers.RotatingFileHandler):
            file_handler = h
            break

    if file_handler is not None:
        file_handler.close()
        logger.removeHandler(file_handler)

    # Truncate main log file and its backup
    try:
        if log_path.exists():
            log_path.write_text("", encoding="utf-8")
        backup = log_path.with_suffix(".log.1")
        if backup.exists():
            backup.unlink()
    except OSError:
        pass

    # Reattach a fresh handler so logging continues
    setup_file_handler(log_path)
