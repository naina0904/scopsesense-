class HotspotEngine:

    # =================================================
    # ANALYZE HOTSPOTS
    # =================================================

    def analyze(

        self,

        feature_ownership,

        timeline_analysis
    ):

        hotspots = []

        # ---------------------------------------------
        # TIMELINE LOOKUP
        # ---------------------------------------------

        timeline_lookup = {

            entry["feature"]:
                entry

            for entry in timeline_analysis
        }

        # ---------------------------------------------
        # PROCESS FEATURES
        # ---------------------------------------------

        for ownership in feature_ownership:

            feature = (

                ownership.get(
                    "feature",
                    ""
                )
            )

            contributors = (

                ownership.get(
                    "contributors",
                    []
                )
            )

            matched_files = (

                ownership.get(
                    "matched_files",
                    []
                )
            )

            ownership_confidence = (

                ownership.get(
                    "ownership_confidence",
                    0
                )
            )

            timeline = (

                timeline_lookup.get(
                    feature,
                    {}
                )
            )

            status = (

                timeline.get(
                    "status",
                    "unknown"
                )
            )

            activity_gaps = (

                timeline.get(
                    "activity_gaps",
                    []
                )
            )

            commit_velocity = (

                timeline.get(
                    "commit_velocity",
                    "unknown"
                )
            )

            # -----------------------------------------
            # HOTSPOT SCORE
            # -----------------------------------------

            hotspot_score = 0

            # -----------------------------------------
            # MULTI-CONTRIBUTOR RISK
            # -----------------------------------------

            if len(contributors) >= 3:

                hotspot_score += 25

            elif len(contributors) == 2:

                hotspot_score += 15

            # -----------------------------------------
            # LOW OWNERSHIP CONFIDENCE
            # -----------------------------------------

            if ownership_confidence <= 25:

                hotspot_score += 30

            elif ownership_confidence <= 50:

                hotspot_score += 15

            # -----------------------------------------
            # CRITICAL TIMELINE DELAY
            # -----------------------------------------

            if status == "critical_delay":

                hotspot_score += 35

            elif status == "moderate_delay":

                hotspot_score += 20

            # -----------------------------------------
            # LARGE ACTIVITY GAPS
            # -----------------------------------------

            largest_gap = 0

            if activity_gaps:

                largest_gap = max(

                    gap["gap_days"]

                    for gap in activity_gaps
                )

            if largest_gap >= 45:

                hotspot_score += 25

            elif largest_gap >= 30:

                hotspot_score += 15

            # -----------------------------------------
            # LOW VELOCITY
            # -----------------------------------------

            if commit_velocity == "low":

                hotspot_score += 15

            # -----------------------------------------
            # FINAL RISK LEVEL
            # -----------------------------------------

            if hotspot_score >= 80:

                risk_level = "critical"

            elif hotspot_score >= 55:

                risk_level = "high"

            elif hotspot_score >= 35:

                risk_level = "moderate"

            else:

                risk_level = "low"

            hotspots.append({

                "feature":
                    feature,

                "matched_files":
                    matched_files,

                "contributors":
                    contributors,

                "risk_level":
                    risk_level,

                "hotspot_score":
                    hotspot_score,

                "largest_activity_gap":
                    largest_gap,

                "timeline_status":
                    status,

                "commit_velocity":
                    commit_velocity
            })

        return hotspots