from datetime import datetime
from collections import defaultdict


class TimelineAnalyzer:

    WORK_HOURS_PER_DAY = 8
    WORK_DAYS_PER_WEEK = 5

    def analyze_commit_activity(self, commits):
        developer_activity = defaultdict(int)

        commit_dates = []

        for commit in commits:
            author = commit["author"]
            developer_activity[author] += 1

            commit_dates.append(
                datetime.fromisoformat(
                    commit["date"].replace("Z", "+00:00")
                )
            )

        if not commit_dates:
            return {
                "total_commits": 0,
                "developers": [],
                "project_start": None,
                "project_end": None
            }

        project_start = min(commit_dates)
        project_end = max(commit_dates)

        duration_days = (project_end - project_start).days + 1

        estimated_work_days = max(
            1,
            int(duration_days * (5 / 7))
        )

        estimated_work_hours = (
            estimated_work_days *
            self.WORK_HOURS_PER_DAY
        )

        return {
            "total_commits": len(commits),
            "developers": dict(developer_activity),
            "project_start": project_start.isoformat(),
            "project_end": project_end.isoformat(),
            "duration_days": duration_days,
            "estimated_work_days": estimated_work_days,
            "estimated_work_hours": estimated_work_hours
        }