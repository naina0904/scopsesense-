import re

from datetime import datetime

from backend.semantic.engineering_calendar_engine import (
    EngineeringCalendarEngine
)


class TimelineEngine:

    # -------------------------------------------------
    # INIT
    # -------------------------------------------------

    def __init__(self):

        self.calendar_engine = (
            EngineeringCalendarEngine()
        )

    # -------------------------------------------------
    # REPOSITORY TIMELINE COMPATIBILITY
    # -------------------------------------------------

    def analyze_timeline(

        self,

        repository
    ):

        try:

            commits = list(
                repository.get_commits()
            )

            dates = []

            for commit in commits:

                commit_date = (
                    commit.commit.author.date
                )

                if commit_date:

                    dates.append(
                        commit_date
                    )

            if not dates:

                return {

                    "total_commits":
                        0,

                    "velocity":
                        "low",

                    "activity_gaps":
                        [],

                    "execution_health": {

                        "status":
                            "unknown"
                    }
                }

            start_date = min(dates)

            end_date = max(dates)

            duration_days = max(

                1,

                (
                    end_date
                    -
                    start_date
                ).days
            )

            commits_per_week = (

                len(dates)
                /
                (duration_days / 7)
            )

            if commits_per_week >= 5:

                velocity = "high"

            elif commits_per_week >= 2:

                velocity = "moderate"

            else:

                velocity = "low"

            sorted_dates = sorted(dates)

            activity_gaps = []

            for idx in range(
                1,
                len(sorted_dates)
            ):

                gap_days = (

                    sorted_dates[idx]
                    -
                    sorted_dates[idx - 1]
                ).days

                if gap_days >= 14:

                    activity_gaps.append({

                        "start":
                            sorted_dates[idx - 1],

                        "end":
                            sorted_dates[idx],

                        "gap_days":
                            gap_days
                    })

            return {

                "total_commits":
                    len(dates),

                "project_start":
                    start_date,

                "project_end":
                    end_date,

                "duration_days":
                    duration_days,

                "commits_per_week":
                    round(
                        commits_per_week,
                        2
                    ),

                "velocity":
                    velocity,

                "activity_gaps":
                    activity_gaps,

                "execution_health": {

                    "status":
                        "healthy"
                        if velocity != "low"
                        else "watch"
                }
            }

        except Exception as e:

            return {

                "error":
                    str(e)
            }

    # -------------------------------------------------
    # SCHEDULE PARSING

    def _parse_date_from_text(

        self,

        text
    ):

        if not text or not isinstance(text, str):

            return None

        text = text.strip()

        date_patterns = [
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{2}/\d{2}/\d{4})",
            r"(\d{2}\.\d{2}\.\d{4})"
        ]

        for pattern in date_patterns:

            match = re.search(pattern, text)

            if match:

                date_value = match.group(1)

                try:

                    if "-" in date_value:

                        return datetime.fromisoformat(
                            date_value
                        )

                    if "/" in date_value:

                        return datetime.strptime(
                            date_value,
                            "%d/%m/%Y"
                        )

                    if "." in date_value:

                        return datetime.strptime(
                            date_value,
                            "%d.%m.%Y"
                        )

                except Exception:

                    continue

        return None

    # -------------------------------------------------
    # SEMANTIC TIMELINE ANALYSIS
    # -------------------------------------------------

    def analyze_semantic_timeline(

        self,

        feature_data,

        repository_start_date,

        actual_completion_date,

        activity_gaps=None,

        commit_velocity="unknown",

        feature_start_date=None,

        feature_actual_completion_date=None,

        feature_ownership_confidence=None,

        planned_start_date=None,

        planned_completion_date=None,

        schedule_source=None,

        matched_issue=None
    ):

        try:

            estimated_hours = (

                feature_data.get(
                    "expected_hours",
                    0
                )
            )

            developers = len(

                feature_data.get(
                    "assigned_developers",
                    []
                )
            )

            if developers <= 0:

                developers = 1

            use_feature_window = (
                feature_start_date is not None
                and feature_actual_completion_date is not None
                and feature_ownership_confidence is not None
                and feature_ownership_confidence >= 70
            )

            start_date = (
                feature_start_date
                if use_feature_window
                else repository_start_date
            )

            end_date = (
                feature_actual_completion_date
                if use_feature_window
                else actual_completion_date
            )

            if isinstance(planned_completion_date, str):

                planned_completion_date = (
                    self._parse_date_from_text(
                        planned_completion_date
                    )
                )

            schedule_delay_days = None

            if planned_completion_date:

                schedule_delay_days = (

                    self.calendar_engine.calculate_delay_days(

                        planned_completion_date,

                        end_date
                    )
                )

            analysis = (

                self.calendar_engine.analyze_effort(

                    estimated_hours=

                        estimated_hours,

                    developers=

                        developers,

                    start_date=

                        start_date,

                    actual_completion=

                        end_date
                )
            )

            timeline_status = (

                self._determine_timeline_status(
                    analysis,
                    schedule_delay_days,
                    commit_velocity
                )
            )

            if activity_gaps:

                largest_gap = max(

                    gap["gap_days"]

                    for gap in activity_gaps
                )

                if largest_gap >= 30:

                    timeline_status = (
                        "critical_delay"
                    )

                elif largest_gap >= 14:

                    if timeline_status != (
                        "critical_delay"
                    ):

                        timeline_status = (
                            "moderate_delay"
                        )

            if commit_velocity == "low":

                if timeline_status == (
                    "on_track"
                ):

                    timeline_status = (
                        "minor_delay"
                    )

            delay_root_cause = (
                "No significant timeline delay detected against the available schedule and effort estimate."
            )

            if schedule_delay_days is not None and schedule_delay_days > 0:

                schedule_reference = (
                    schedule_source or "planned schedule"
                )

                issue_reference = ""

                if matched_issue and matched_issue.get("title"):

                    issue_reference = (
                        f" for issue #{matched_issue.get('number')}: "
                        f"{matched_issue.get('title')}"
                    )

                delay_root_cause = (
                    f"Actual completion missed the {schedule_reference}"
                    f"{issue_reference} by {schedule_delay_days} workday(s)."
                )

            elif analysis.get("delay_days", 0) > 0:

                delay_root_cause = (
                    "Actual completion exceeded the SRS effort estimate based on available feature hours."
                )

            elif commit_velocity == "low":

                delay_root_cause = (
                    "Low commit velocity may have contributed to schedule drift."
                )

            matched_issue_summary = None

            if matched_issue:

                matched_issue_summary = {

                    "title":
                        matched_issue.get("title"),

                    "number":
                        matched_issue.get("number"),

                    "state":
                        matched_issue.get("state")
                }

            return {

                "feature":

                    feature_data.get(
                        "feature_name"
                    ),

                "timeline_analysis":

                    analysis,

                "activity_gaps":

                    activity_gaps,

                "commit_velocity":

                    commit_velocity,

                "feature_start_date":

                    start_date,

                "feature_actual_completion_date":

                    end_date,

                "planned_start_date":

                    planned_start_date,

                "planned_completion_date":

                    planned_completion_date,

                "schedule_source":

                    schedule_source,

                "matched_issue":

                    matched_issue_summary,

                "schedule_delay_days":

                    schedule_delay_days,

                "delay_root_cause":

                    delay_root_cause,

                "timeline_date_source":
                    (
                        "feature_specific"
                        if use_feature_window
                        else "repository_wide"
                    ),

                "status":
                    timeline_status
            }

        except Exception as e:

            return {

                "error":
                    str(e)
            }

    # -------------------------------------------------
    # TIMELINE STATUS
    # -------------------------------------------------

    def _determine_timeline_status(

        self,

        analysis,

        schedule_delay_days=None,

        commit_velocity="unknown"
    ):

        delay_days = analysis.get(
            "delay_days",
            0
        )

        if schedule_delay_days is not None and schedule_delay_days > 0:

            return "delayed"

        if delay_days == 0:

            if commit_velocity == "low":

                return "minor_delay"

            return "on_track"

        if delay_days <= 5:

            return "minor_delay"

        if delay_days <= 15:

            return "moderate_delay"

        return "critical_delay"
