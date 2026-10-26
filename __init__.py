"""Birthday Wishes — Vestaboard Note plugin for multiple birthdays."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)

NOTE_WIDTH = 15
NOTE_ROWS = 3

RED = "{63}"
ORANGE = "{64}"
YELLOW = "{65}"
GREEN = "{66}"
BLUE = "{67}"
VIOLET = "{68}"
WHITE = "{69}"

# Festive colour pairs for the Note
COLOUR_SETS = [
    (YELLOW, VIOLET),
    (RED, YELLOW),
    (VIOLET, ORANGE),
    (ORANGE, RED),
    (YELLOW, RED),
]


def _tile_len(s: str) -> int:
    codes = re.findall(r"\{\d{2}\}", s)
    stripped = re.sub(r"\{\d{2}\}", "", s)
    return len(stripped) + len(codes)


def _pad(s: str, width: int = NOTE_WIDTH) -> str:
    return (s or "")[:width].ljust(width)


def _parse_people(raw: str) -> List[Dict[str, Any]]:
    """
    Parse birthday list. Accepted lines:

      Alice Smith, 15/03
      Bob Jones, 1990-03-22
      Carol, 3-15
      Dave Brown | 25 December

    Returns list of dicts with forename, surname, day, month, sort_key.
    """
    people: List[Dict[str, Any]] = []
    if not raw or not str(raw).strip():
        return people

    for line in str(raw).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Split name from date
        if "|" in line:
            name_part, date_part = line.split("|", 1)
        elif "," in line:
            name_part, date_part = line.split(",", 1)
        else:
            continue

        name_part = name_part.strip()
        date_part = date_part.strip()
        if not name_part or not date_part:
            continue

        tokens = name_part.split()
        forename = tokens[0] if tokens else name_part
        surname = " ".join(tokens[1:]) if len(tokens) > 1 else ""

        day, month = _parse_day_month(date_part)
        if day is None or month is None:
            continue

        people.append(
            {
                "forename": forename[:20],
                "surname": surname[:20],
                "full_name": name_part[:40],
                "day": day,
                "month": month,
                "day_str": str(day),
                "month_str": str(month),
                "month_name": date(2000, month, 1).strftime("%B"),
                "month_name_short": date(2000, month, 1).strftime("%b"),
            }
        )
    return people


def _parse_day_month(s: str) -> Tuple[Optional[int], Optional[int]]:
    s = s.strip()
    # ISO or yyyy-mm-dd / mm-dd
    m = re.match(r"^(?:(\d{4})[-/])?(\d{1,2})[-/](\d{1,2})$", s)
    if m:
        # group2=month, group3=day if year-month-day or month-day
        # Actually: (year)? month day  — but UK often day/month
        # Try both heuristics below
        pass

    # day/month or day-month (UK style preferred)
    m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        # If a > 12, must be day/month
        if a > 12 and 1 <= b <= 12:
            return a, b
        # If b > 12, must be month/day
        if b > 12 and 1 <= a <= 12:
            return b, a
        # Ambiguous: prefer day/month (UK)
        if 1 <= a <= 31 and 1 <= b <= 12:
            return a, b

    # "25 December" / "25 Dec" / "December 25"
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)", s)
    if m:
        day = int(m.group(1))
        mon = _month_from_name(m.group(2))
        if mon:
            return day, mon
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})", s)
    if m:
        mon = _month_from_name(m.group(1))
        day = int(m.group(2))
        if mon:
            return day, mon

    # yyyy-mm-dd
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        return int(m.group(3)), int(m.group(2))

    return None, None


def _month_from_name(name: str) -> Optional[int]:
    name = name.strip().lower()[:3]
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    return months.get(name)



def _load_birthdays_text(config: Dict[str, Any]) -> str:
    """Load birthday list from optional host file path, else text setting.

    Import format (one person per line):
        Alice Smith, 15/03
        Bob Jones, 22/06

    Lines starting with # are comments. If birthdays_file is set and readable,
    it takes priority over the birthdays text box.
    """
    file_path = (config.get("birthdays_file") or "").strip()
    if file_path:
        try:
            p = Path(file_path).expanduser()
            if p.is_file():
                return p.read_text(encoding="utf-8", errors="replace")
            logger.warning("birthdays_file not found or not a file: %s", file_path)
        except OSError as e:
            logger.warning("Could not read birthdays_file %s: %s", file_path, e)
    return config.get("birthdays", "") or ""


def _days_until(day: int, month: int, today: date) -> int:
    try:
        this_year = date(today.year, month, day)
    except ValueError:
        # Feb 29 non-leap: use Feb 28
        this_year = date(today.year, month, min(day, 28))
    if this_year >= today:
        return (this_year - today).days
    try:
        next_year = date(today.year + 1, month, day)
    except ValueError:
        next_year = date(today.year + 1, month, min(day, 28))
    return (next_year - today).days


def _format_note(
    forename: str,
    is_today: bool,
    days_until: int,
    colour_idx: int = 0,
) -> Tuple[str, str, str, str, str, str]:
    """
    Attractive 15×3 Birthday Note.

      {65}{68} HAPPY
      BIRTHDAY
         ALICE
    """
    c1, c2 = COLOUR_SETS[colour_idx % len(COLOUR_SETS)]
    name = (forename or "FRIEND").upper().strip()[:NOTE_WIDTH]

    line_happy = " HAPPY"
    row1 = f"{c1}{c2}{line_happy[:13].ljust(13)}"
    while _tile_len(row1) > NOTE_WIDTH:
        line_happy = line_happy[:-1]
        row1 = f"{c1}{c2}{line_happy[:13].ljust(13)}"

    row2 = _pad("BIRTHDAY")
    # Center forename on row 3 when short
    if len(name) < NOTE_WIDTH:
        row3 = name.center(NOTE_WIDTH)[:NOTE_WIDTH]
    else:
        row3 = name[:NOTE_WIDTH]
    row3 = _pad(row3)

    # Optional tiny status if not today and room — prefer name only on birthday
    # Keep pure celebratory layout when today
    if not is_today and days_until == 1:
        # Tomorrow: still show name; status not needed on Note
        pass

    block = f"{row1}\n{row2}\n{row3}"
    return block, row1, row2, row3, c1, c2


def _happy_block(forename: str) -> str:
    """Single-line style block: Happy Birthday [forename] (for templates)."""
    fn = (forename or "Friend").strip()
    msg = f"Happy Birthday {fn}"
    return msg[:60]


class BirthdayWishesPlugin(PluginBase):
    """Show Happy Birthday for people whose birthday is today (or next)."""

    @property
    def plugin_id(self) -> str:
        return "birthday_wishes"

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        mode = config.get("display_mode", "today_or_next")
        if mode not in ("today_only", "today_or_next"):
            errors.append("display_mode must be today_only or today_or_next")
        refresh = config.get("refresh_seconds", 3600)
        if not isinstance(refresh, int) or refresh < 300:
            errors.append("refresh_seconds must be an integer >= 300")
        return errors

    def on_config_change(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        try:
            self.clear_cache()
        except Exception:
            pass

    def fetch_data(self) -> PluginResult:
        try:
            raw = _load_birthdays_text(self.config)
            mode = self.config.get("display_mode", "today_or_next")
            today = datetime.now(timezone.utc).date()

            people = _parse_people(raw)
            if not people:
                return PluginResult(
                    available=False,
                    error="No birthdays configured — use list or file (Alice Smith, 15/03)",
                )

            enriched = []
            for i, p in enumerate(people):
                du = _days_until(p["day"], p["month"], today)
                enriched.append({**p, "days_until": du, "is_today": du == 0, "index": i})

            today_list = [p for p in enriched if p["is_today"]]
            future = sorted(
                [p for p in enriched if p["days_until"] > 0],
                key=lambda x: x["days_until"],
            )

            if today_list:
                # Rotate among today's birthdays by day-of-year + index
                pick = today_list[today.toordinal() % len(today_list)]
            elif mode == "today_or_next" and future:
                pick = future[0]
            else:
                return PluginResult(
                    available=False,
                    error="No birthday today",
                    data={"is_today": "NO", "has_birthday": "NO"},
                )

            block, r1, r2, r3, c1, c2 = _format_note(
                pick["forename"],
                pick["is_today"],
                pick["days_until"],
                colour_idx=pick["index"],
            )
            r2 = _pad(r2)
            r3 = _pad(r3)
            block = f"{r1}\n{r2}\n{r3}"

            happy = _happy_block(pick["forename"])
            # Note-friendly happy lines (≤15 each)
            happy_r1 = _pad("HAPPY BIRTHDAY")
            happy_r2 = _pad(pick["forename"].upper()[:15])
            happy_r3 = _pad("" if pick["is_today"] else f"IN {pick['days_until']}D")

            # All people for array variable
            people_out = []
            for p in sorted(enriched, key=lambda x: (x["days_until"], x["forename"])):
                people_out.append(
                    {
                        "forename": p["forename"][:20],
                        "surname": p["surname"][:20],
                        "full_name": p["full_name"][:40],
                        "day": p["day_str"][:2],
                        "month": p["month_str"][:2],
                        "month_name": p["month_name"][:10],
                        "days_until": str(p["days_until"]),
                        "is_today": "YES" if p["is_today"] else "NO",
                    }
                )

            data = {
                "forename": pick["forename"][:20],
                "surname": pick["surname"][:20],
                "full_name": pick["full_name"][:40],
                "day": pick["day_str"][:2],
                "month": pick["month_str"][:2],
                "month_name": pick["month_name"][:10],
                "month_name_short": pick["month_name_short"][:3],
                "is_today": "YES" if pick["is_today"] else "NO",
                "has_birthday": "YES",
                "days_until": str(pick["days_until"]),
                "color": c1,
                "color2": c2,
                "note_row1": r1,
                "note_row2": r2,
                "note_row3": r3,
                "note_block": block,
                "happy_birthday": happy[:45],
                "happy_block": happy[:45],
                "happy_row1": happy_r1,
                "happy_row2": happy_r2,
                "happy_row3": happy_r3,
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                "people": people_out,
                "people_count": str(len(people_out)),
            }
            return PluginResult(available=True, data=data)
        except Exception as e:
            logger.exception("birthday_wishes error")
            return PluginResult(available=False, error=str(e)[:120])
