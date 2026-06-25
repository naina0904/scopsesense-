from typing import Union

from backend.models.calendar_profile import CalendarProfile

class EffortNormalizer:
    """Normalize effort values expressed in various units to a common *hours* unit.

    The conversion respects the ``CalendarProfile`` configuration:

    * ``hours_per_day`` – standard productive hours in a working day.
    * ``working_days`` – number of working days in a week (e.g., [0,1,2,3,4] for Mon‑Fri).
    * ``holidays`` – ignored in this simple conversion (placeholder for future expansion).
    """

    UNIT_MAP = {
        "minute": 1 / 60,
        "minutes": 1 / 60,
        "hour": 1,
        "hours": 1,
        "day": None,  # resolved via profile.hours_per_day
        "days": None,
        "week": None,  # resolved via len(profile.working_days) * hours_per_day
        "weeks": None,
        "month": None,  # approximated as 4 weeks
        "months": None,
    }

    def __init__(self, profile: CalendarProfile):
        self.profile = profile
        # Pre‑compute week and month multipliers
        self.week_multiplier = len(profile.working_days) * profile.hours_per_day
        self.month_multiplier = self.week_multiplier * 4  # simplistic 4‑week month

    def normalize(self, value: Union[int, float], unit: str) -> float:
        """Convert ``value`` expressed in ``unit`` to hours.

        Parameters
        ----------
        value: int | float
            The raw effort amount.
        unit: str
            One of ``minute(s)``, ``hour(s)``, ``day(s)``, ``week(s)``, ``month(s)``.

        Returns
        -------
        float
            Effort expressed in hours.
        """
        unit = unit.strip().lower()
        if unit not in self.UNIT_MAP:
            raise ValueError(f"Unsupported effort unit: {unit}")

        multiplier = self.UNIT_MAP[unit]
        if multiplier is not None:
            # minute or hour based conversion
            return float(value) * multiplier

        # Day based conversion
        if unit in ("day", "days"):
            return float(value) * self.profile.hours_per_day
        if unit in ("week", "weeks"):
            return float(value) * self.week_multiplier
        if unit in ("month", "months"):
            return float(value) * self.month_multiplier
        # Fallback – should never reach here
        raise ValueError(f"Unable to normalize unit: {unit}")
