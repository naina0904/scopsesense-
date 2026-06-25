from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CalendarProfile:
    """Configuration that determines how effort units are converted to hours.

    Attributes
    ----------
    working_days: List[int]
        Weekday numbers (0=Monday .. 6=Sunday) that are considered working days.
    hours_per_day: float
        Standard number of productive hours in a working day.
    holidays: List[str]
        Dates (ISO ``YYYY-MM-DD``) that are treated as non‑working days.
    timezone: str
        IANA timezone name, e.g. ``"America/New_York"``.
    """

    working_days: List[int]
    hours_per_day: float
    holidays: List[str]
    timezone: str
