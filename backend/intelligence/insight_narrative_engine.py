class InsightNarrativeEngine:

    def __init__(
        self,
        llm_manager=None
    ):
        self.llm_manager = llm_manager

    # =================================================
    # GENERATE INSIGHTS
    # =================================================

    def generate(

        self,

        hotspots,

        causality
    ):

        insights = []

        for hotspot in hotspots:

            feature = (

                hotspot.get(
                    "feature",
                    "Unknown Feature"
                )
            )

            risk_level = (

                hotspot.get(
                    "risk_level",
                    "unknown"
                )
            )

            largest_gap = (

                hotspot.get(
                    "largest_activity_gap",
                    0
                )
            )

            contributors = (

                hotspot.get(
                    "contributors",
                    []
                )
            )

            commit_velocity = (

                hotspot.get(
                    "commit_velocity",
                    "unknown"
                )
            )

            # -----------------------------------------
            # BUILD INSIGHT
            # -----------------------------------------

            # Build a richer, human‑readable narrative.
            # If we have enough deterministic evidence we synthesize a concise paragraph.
            # Otherwise we fall back to a safe generic statement.
            if risk_level != "unknown" and (largest_gap or commit_velocity != "unknown" or contributors):
                parts = []
                # risk level description
                parts.append(f"The **{feature}** component exhibits a **{risk_level}** engineering risk.")
                # inactivity gap
                if largest_gap and largest_gap >= 45:
                    parts.append(f"A {largest_gap}-day inactivity gap was detected, indicating periods of low activity.")
                # commit velocity
                if commit_velocity and commit_velocity != "unknown":
                    parts.append(f"Commit velocity is **{commit_velocity}**, suggesting {commit_velocity} development pace.")
                # ownership distribution
                if contributors and len(contributors) >= 2:
                    joined = ", ".join(contributors)
                    parts.append(f"Ownership is distributed across {joined}.")
                narrative = " ".join(parts)
            else:
                # Graceful fallback when data is sparse
                narrative = f"No significant engineering instability was detected for **{feature}** during the audit period."

            evidence = []

            # -----------------------------------------
            # GAP ANALYSIS
            # -----------------------------------------

            if largest_gap and largest_gap >= 45:

                evidence.append(

                    f"{largest_gap}-day inactivity gap detected"
                )

            # -----------------------------------------
            # VELOCITY
            # -----------------------------------------

            if commit_velocity and commit_velocity != "unknown":

                evidence.append(

                    f"Commit velocity is **{commit_velocity}**"
                )

            # -----------------------------------------
            # OWNERSHIP
            # -----------------------------------------

            if contributors and len(contributors) >= 2:

                joined = ", ".join(
                    contributors
                )

                evidence.append(

                    f"Ownership distributed across {joined}"
                )

            # -----------------------------------------
            # RECOMMENDATION
            # -----------------------------------------

            recommendation = (

                "Stabilize ownership boundaries "
                "and reduce execution delays "
                "before expanding feature scope."
            )

            insights.append({

                "feature":
                    feature,

                "narrative":
                    narrative,

                "evidence":
                    evidence,

                "recommendation":
                    recommendation
            })

        return insights