"""Helper functions for Desktop Icon Backup Manager"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Optional, Tuple

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QCoreApplication  # noqa: F401  (re-exported for callers)

# ── Canonical backup filename format ──────────────────────────────────────────
#
# <WIDTH>x<HEIGHT>_<YYYYMMDD>_<HHMMSS>.json
#
# Examples:
#   1920x1080_20240815_143005.json
#   3840x2160_20241231_235959.json
#
# Parsed with a strict regex that fails fast on malformed input.
_BACKUP_FILENAME_RE = re.compile(
    r"""
    \A
    (?P<res>\d+x\d+)        # 1920x1080
    _
    (?P<date>\d{8})         # YYYYMMDD
    _
    (?P<time>\d{6})         # HHMMSS
    \.json
    \Z
    """,
    re.VERBOSE,
)

# Resolution is a pair of positive decimal integers separated by a lowercase
# 'x'. No whitespace, no uppercase 'X', no extra components.
_RESOLUTION_RE = re.compile(r"\A(?P<w>\d+)x(?P<h>\d+)\Z")


# ── Display metadata ──────────────────────────────────────────────────────────
def get_display_metadata() -> Dict:
    """Get metadata about connected displays"""
    app = QApplication.instance()
    if not app:
        return {
            "monitor_count": 0,
            "screens": [],
            "primary_resolution": "UnknownResolution",
        }

    screens = QGuiApplication.screens()
    metadata: Dict = {
        "monitor_count": len(screens),
        "screens": [
            {
                "id": i,
                "name": s.name(),
                "width": round(s.geometry().width() * s.devicePixelRatio()),
                "height": round(s.geometry().height() * s.devicePixelRatio()),
                "pixel_density": s.devicePixelRatio(),
            }
            for i, s in enumerate(screens)
        ],
    }

    if screens:
        primary_screen = QGuiApplication.primaryScreen()
        dpr = primary_screen.devicePixelRatio() or 1.0
        primary_w = round(primary_screen.geometry().width() * dpr)
        primary_h = round(primary_screen.geometry().height() * dpr)
        metadata["primary_resolution"] = f"{primary_w}x{primary_h}"
    else:
        metadata["primary_resolution"] = "UnknownResolution"
    return metadata


# ── Backup filename parsing ───────────────────────────────────────────────────
def parse_backup_filename(filename: str) -> Tuple[str, str, str]:
    """
    Parse a backup filename and return ``(readable_date, resolution, timestamp_part)``.

    The only accepted shape is ``<WIDTH>x<HEIGHT>_<YYYYMMDD>_<HHMMSS>.json``.
    Any filename that does not match this exact pattern — or whose date and
    time components do not form a real calendar date — is considered
    malformed and returns ``("N/A", "N/A", "N/A")``.
    """
    match = _BACKUP_FILENAME_RE.match(filename)
    if match is None:
        return "N/A", "N/A", "N/A"

    resolution = match.group("res")
    timestamp_part = f"{match.group('date')}_{match.group('time')}"

    try:
        dt_object = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
    except ValueError:
        # Regex-valid but calendrically impossible (e.g. 20240230_143005)
        return "N/A", "N/A", "N/A"

    readable_date = dt_object.strftime("%Y/%m/%d %H:%M:%S")
    return readable_date, resolution, timestamp_part


# ── Resolution parsing ────────────────────────────────────────────────────────
def parse_resolution_string(resolution_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse a resolution string like ``"1920x1080"`` into ``(1920, 1080)``.

    The input must match ``<digits>x<digits>`` exactly, with a lowercase
    ``x`` separator and no whitespace. Returns ``None`` for anything else,
    including positive-but-zero values (``"0x0"`` is rejected — a real
    display cannot have a zero-pixel dimension).
    """
    if not isinstance(resolution_str, str):
        return None

    match = _RESOLUTION_RE.match(resolution_str)
    if match is None:
        return None

    width = int(match.group("w"))
    height = int(match.group("h"))
    if width <= 0 or height <= 0:
        return None
    return width, height


# ── Convenience wrappers ──────────────────────────────────────────────────────
def get_readable_date(filename: str) -> str:
    """Extract the readable date from a backup filename."""
    return parse_backup_filename(filename)[0]


def get_resolution_from_filename(filename: str) -> str:
    """Extract the resolution from a backup filename."""
    return parse_backup_filename(filename)[1]
