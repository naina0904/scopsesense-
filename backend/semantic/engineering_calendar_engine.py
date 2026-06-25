from datetime import (
    datetime,
    date,
    timedelta
)

from math import ceil


class EngineeringCalendarEngine:

    # =========================================
    # CONFIGURATION
    # =========================================

    HOURS_PER_DAY = 8

    WORK_DAYS_PER_WEEK = 5

    HOURS_PER_WEEK = (
        HOURS_PER_DAY *
        WORK_DAYS_PER_WEEK
    )

    def __init__(self, holidays=None):
        self.holidays = set()
        if holidays:
            for holiday in holidays:
                if isinstance(holiday, datetime):
                    self.holidays.add(holiday.date())
                elif isinstance(holiday, date):
                    self.holidays.add(holiday)

    # =========================================
    # WORKDAY CHECK
    # =========================================

    def is_workday(

        self,

        date: datetime
    ) -> bool:

        if date.weekday() >= 5:
            return False

        return date.date() not in self.holidays

    # =========================================
    # NEXT WORKDAY
    # =========================================

    def next_workday(

        self,

        date: datetime
    ) -> datetime:

        current = date

        while not self.is_workday(current):

            current += timedelta(days=1)

        return current

    # =========================================
    # ADD WORKDAYS
    # =========================================

    def add_workdays(

        self,

        start_date: datetime,

        workdays: int
    ) -> datetime:

        current = self.next_workday(
            start_date
        )

        added_days = 0

        while added_days < workdays:

            current += timedelta(days=1)

            if self.is_workday(current):

                added_days += 1

        return current

    # =========================================
    # TEAM DAILY CAPACITY
    # =========================================

    def calculate_team_capacity(

        self,

        developers: int
    ) -> int:

        if developers <= 0:

            developers = 1

        return (
            developers *
            self.HOURS_PER_DAY
        )

    # =========================================
    # ESTIMATE WORKDAYS
    # =========================================

    def estimate_workdays(

        self,

        estimated_hours: int,

        developers: int = 1
    ) -> int:

        team_capacity = (

            self.calculate_team_capacity(
                developers
            )
        )

        estimated_days = (

            estimated_hours /
            team_capacity
        )

        return ceil(
            estimated_days
        )

    # =========================================
    # ESTIMATE COMPLETION DATE
    # =========================================

    def estimate_completion_date(

        self,

        start_date: datetime,

        estimated_hours: int,

        developers: int = 1
    ) -> datetime:

        required_days = (

            self.estimate_workdays(

                estimated_hours,

                developers
            )
        )

        return self.add_workdays(

            start_date,

            required_days
        )

    # =========================================
    # CALCULATE WORKING DAY DELAY
    # =========================================

    def calculate_delay_days(

        self,

        expected_date: datetime,

        actual_date: datetime
    ) -> int:

        if actual_date <= expected_date:

            return 0

        delay = 0

        current = expected_date

        while current < actual_date:

            current += timedelta(days=1)

            if self.is_workday(current):

                delay += 1

        return delay

    # =========================================
    # EFFORT ANALYSIS
    # =========================================

    def analyze_effort(

        self,

        estimated_hours: int,

        developers: int,

        start_date: datetime,

        actual_completion: datetime
    ) -> dict:

        expected_completion = (

            self.estimate_completion_date(

                start_date,

                estimated_hours,

                developers
            )
        )

        delay_days = (

            self.calculate_delay_days(

                expected_completion,

                actual_completion
            )
        )

        return {

            "estimated_hours":
                estimated_hours,

            "developers":
                developers,

            "expected_completion":
                expected_completion,

            "actual_completion":
                actual_completion,

            "delay_days":
                delay_days,

            "estimated_workdays":

                self.estimate_workdays(

                    estimated_hours,

                    developers
                )
        }