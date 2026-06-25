from datetime import (
    datetime,
    timezone
)

import json

from pathlib import Path


class RepositoryMemory:

    # -------------------------------------------------
    # INIT
    # -------------------------------------------------

    def __init__(self):

        self.memory_dir = Path(
            "backend/memory/storage"
        )

        self.memory_dir.mkdir(

            parents=True,
            exist_ok=True
        )

    # -------------------------------------------------
    # MEMORY PATH
    # -------------------------------------------------

    def _memory_path(

        self,
        owner,
        repo
    ):

        filename = (
            f"{owner}_{repo}.json"
        )

        return self.memory_dir / filename

    # -------------------------------------------------
    # SAVE SNAPSHOT
    # -------------------------------------------------

    def save_snapshot(

        self,
        owner,
        repo,
        repository_data
    ):

        path = self._memory_path(
            owner,
            repo
        )

        memory = self.load_memory(
            owner,
            repo
        )

        snapshot = {

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "data":
                repository_data
        }

        memory.append(snapshot)

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(

                memory,

                f,

                indent=2
            )

    # -------------------------------------------------
    # LOAD MEMORY
    # -------------------------------------------------

    def load_memory(

        self,
        owner,
        repo
    ):

        path = self._memory_path(
            owner,
            repo
        )

        if not path.exists():

            return []

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    # -------------------------------------------------
    # LATEST SNAPSHOT
    # -------------------------------------------------

    def latest_snapshot(

        self,
        owner,
        repo
    ):

        memory = self.load_memory(
            owner,
            repo
        )

        if len(memory) == 0:

            return None

        return memory[-1]

    # -------------------------------------------------
    # EXECUTION HISTORY
    # -------------------------------------------------

    def execution_history(

        self,
        owner,
        repo
    ):

        memory = self.load_memory(
            owner,
            repo
        )

        history = []

        for snapshot in memory:

            data = snapshot["data"]

            history.append({

                "timestamp":
                    snapshot["timestamp"],

                "execution_health":

                    data.get(
                        "timeline",
                        {}
                    ).get(
                        "execution_health",
                        {}
                    ),

                "velocity":

                    data.get(
                        "timeline",
                        {}
                    ).get(
                        "velocity",
                        "unknown"
                    ),

                "overall_risk":

                    data.get(
                        "risk_analysis",
                        {}
                    ).get(
                        "overall_risk",
                        "unknown"
                    )
            })

        return history

    # -------------------------------------------------
    # COMPARE SNAPSHOTS
    # -------------------------------------------------

    def compare(

        self,

        previous_audit,

        current_audit
    ):

        insights = []

        previous_velocity = (

            previous_audit
            .get(
                "timeline",
                {}
            )
            .get(
                "velocity",
                "unknown"
            )
        )

        current_velocity = (

            current_audit
            .get(
                "timeline",
                {}
            )
            .get(
                "velocity",
                "unknown"
            )
        )

        if previous_velocity != current_velocity:

            insights.append(

                f"Delivery velocity changed "
                f"from "
                f"'{previous_velocity}' "
                f"to "
                f"'{current_velocity}'."
            )

        previous_risk = (

            previous_audit
            .get(
                "risk_analysis",
                {}
            )
            .get(
                "overall_risk",
                "unknown"
            )
        )

        current_risk = (

            current_audit
            .get(
                "risk_analysis",
                {}
            )
            .get(
                "overall_risk",
                "unknown"
            )
        )

        if previous_risk != current_risk:

            insights.append(

                f"Operational risk changed "
                f"from "
                f"'{previous_risk}' "
                f"to "
                f"'{current_risk}'."
            )

        if len(insights) == 0:

            insights.append(

                "No major operational changes detected."
            )

        return {

            "comparison_insights":
                insights
        }