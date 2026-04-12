"""Single instance guard using a Win32 named mutex (primary) with
QSharedMemory as fallback for non-Windows platforms.

Prevents multiple copies of the application from running simultaneously,
which could cause backup file corruption or conflicting Win32 API calls.

Usage in main.py:
    from utils.single_instance import ensure_single_instance
    lock = ensure_single_instance(app)   # returns None and shows a dialog if already running
    if lock is None:
        sys.exit(0)
    # ... run the app ...
    # lock is released automatically when the process exits
"""

import sys

from PyQt6.QtWidgets import QMessageBox

_MUTEX_NAME = "Global\\DesktopIconBackupManager_SingleInstance_v1"
_APP_KEY = "DesktopIconBackupManager_SingleInstance_v1"

_MSG_TITLE = "Desktop Icon Backup Manager"
_MSG_BODY = (
    "Another instance of the application is already running.\n\n"
    "Check the system tray for the running instance."
)


# ── Win32 mutex implementation ────────────────────────────────────────────────


class _Win32Lock:
    """Holds a Win32 named mutex for the lifetime of the process."""

    def __init__(self, handle):
        self._handle = handle

    def release(self):
        if self._handle is not None:
            try:
                import ctypes

                ctypes.windll.kernel32.CloseHandle(self._handle)
            except Exception:
                pass
            self._handle = None

    def __del__(self):
        self.release()


def _try_win32_lock():
    """
    Try to create a named Win32 mutex.

    Returns a *_Win32Lock* if we are the first instance, or *None* if
    another instance already owns the mutex.
    Returns the string "unavailable" if the Win32 API is not accessible.
    """
    try:
        import ctypes

        ERROR_ALREADY_EXISTS = 183

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)

        if handle == 0:
            return "unavailable"

        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return None

        return _Win32Lock(handle)

    except (AttributeError, OSError):
        return "unavailable"


# ── QSharedMemory fallback ────────────────────────────────────────────────────


class _ShmLock:
    """RAII-style lock: keeps QSharedMemory attached while alive."""

    def __init__(self, shm):
        self._shm = shm

    def release(self):
        try:
            if self._shm and self._shm.isAttached():
                self._shm.detach()
        except RuntimeError:
            pass
        self._shm = None

    def __del__(self):
        self.release()


def _try_shm_lock():
    from PyQt6.QtCore import QSharedMemory

    shm = QSharedMemory(_APP_KEY)
    if shm.attach():
        shm.detach()
    if shm.create(1):
        return _ShmLock(shm)
    return None


# ── Public API ────────────────────────────────────────────────────────────────


def ensure_single_instance(app) -> object | None:
    """
    Try to acquire a single-instance lock.

    On Windows the primary mechanism is a named Win32 mutex, which works
    correctly even with PyInstaller console=False builds. QSharedMemory
    is used as a fallback on other platforms.

    Returns a lock object on success — caller must keep a reference to
    this object for the lifetime of the application.

    Returns None if another instance is already running (a warning
    dialog is shown to the user automatically).
    """
    result = _try_win32_lock()

    if result == "unavailable":
        result = _try_shm_lock()

    if result is None:
        QMessageBox.warning(None, _MSG_TITLE, _MSG_BODY)

    return result
