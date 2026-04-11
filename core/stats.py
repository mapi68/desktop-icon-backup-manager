"""Statistics engine for the Dashboard.

All heavy computation lives here, separate from the UI.
Every function takes the backup directory path and returns plain dicts/lists
that the dialog can render directly.
"""

import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from utils.helpers import parse_backup_filename, get_resolution_from_filename

# ── Public API ────────────────────────────────────────────────────────────────


def compute_all(backup_dir: str) -> Dict:
    """
    Compute every statistic in a single pass over the backup folder.

    Returns a dict with keys:
        file_count, total_bytes, avg_icons,
        first_date, last_date,
        backups_per_month   : list of (YYYY-MM, count) newest-last
        top_resolutions     : list of (res_str, count) most-common-first
        top_tags            : list of (tag, count) most-common-first
        most_moved_icons    : list of (icon_name, times_moved) top-N
    """
    files = _sorted_backup_files(backup_dir)
    if not files:
        return _empty()

    total_bytes = 0
    icon_counts: List[int] = []
    months: List[str] = []
    resolutions: List[str] = []
    tags: List[str] = []
    all_icon_snapshots: List[Dict[str, Tuple[int, int]]] = []
    first_date: Optional[str] = None
    last_date: Optional[str] = None

    for fn in files:
        fp = os.path.join(backup_dir, fn)
        try:
            total_bytes += os.path.getsize(fp)
        except OSError:
            pass

        readable_date, resolution, ts_part = parse_backup_filename(fn)

        # Extract month from the timestamp part (YYYYMMDD_HHMMSS)
        try:
            dt = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
            month_key = dt.strftime("%Y-%m")
            months.append(month_key)
            date_str = dt.strftime("%Y/%m/%d")
            if first_date is None:
                first_date = date_str
            last_date = date_str
        except ValueError:
            pass

        if resolution and resolution != "N/A":
            resolutions.append(resolution)

        # Read JSON content
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "icons" in data:
                icons = data["icons"]
                icon_counts.append(len(icons))
                tag = data.get("description", "").strip()
                if tag:
                    tags.append(tag)
                # Store snapshot for movement analysis
                all_icon_snapshots.append(icons)
            elif isinstance(data, dict):
                # Legacy format: top-level dict of name -> [x,y]
                icon_counts.append(len(data))
                all_icon_snapshots.append(data)
        except (OSError, json.JSONDecodeError):
            pass

    # ── Aggregations ──────────────────────────────────────────────────────

    # Backups per month — last 6 months
    month_counter = Counter(months)
    unique_months = sorted(month_counter.keys())
    backups_per_month = [(m, month_counter[m]) for m in unique_months[-6:]]

    # Top resolutions
    res_counter = Counter(resolutions)
    top_resolutions = res_counter.most_common(5)

    # Top tags
    tag_counter = Counter(tags)
    top_tags = tag_counter.most_common(5)

    # Average icon count
    avg_icons = round(sum(icon_counts) / len(icon_counts)) if icon_counts else 0

    # Most moved icons (compare consecutive snapshots)
    most_moved = _compute_most_moved(all_icon_snapshots, top_n=5)

    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "avg_icons": avg_icons,
        "first_date": first_date or "N/A",
        "last_date": last_date or "N/A",
        "backups_per_month": backups_per_month,
        "top_resolutions": top_resolutions,
        "top_tags": top_tags,
        "most_moved_icons": most_moved,
    }


# ── Internals ─────────────────────────────────────────────────────────────────


def _sorted_backup_files(backup_dir: str) -> List[str]:
    """Return .json filenames sorted oldest-first."""
    if not os.path.isdir(backup_dir):
        return []
    files = [f for f in os.listdir(backup_dir) if f.endswith(".json")]
    files.sort(key=lambda f: parse_backup_filename(f)[2])
    return files


def _compute_most_moved(
    snapshots: List[Dict[str, Tuple[int, int]]], top_n: int = 5
) -> List[Tuple[str, int]]:
    """
    Compare consecutive snapshots and count how many times each icon
    has moved (position changed by more than 4px in either axis).
    """
    move_counter: Counter = Counter()
    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]
        for name, pos in curr.items():
            if name in prev:
                old = prev[name]
                # Positions can be lists or tuples
                ox, oy = old[0], old[1]
                nx, ny = pos[0], pos[1]
                if abs(nx - ox) > 4 or abs(ny - oy) > 4:
                    move_counter[name] += 1
    return move_counter.most_common(top_n)


def _empty() -> Dict:
    """Return an empty stats dict."""
    return {
        "file_count": 0,
        "total_bytes": 0,
        "avg_icons": 0,
        "first_date": "N/A",
        "last_date": "N/A",
        "backups_per_month": [],
        "top_resolutions": [],
        "top_tags": [],
        "most_moved_icons": [],
    }


def format_bytes(n: int) -> str:
    """Human-readable file size."""
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    else:
        return f"{n / (1024 * 1024):.1f} MB"
