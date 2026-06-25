class ContributorIntelligenceEngine:

    # -------------------------------------------------
    # MAIN ANALYSIS
    # -------------------------------------------------

    def analyze(

        self,

        context
    ):

        contributors = context.get(
            "contributors",
            []
        )

        activity = context.get(
            "activity",
            []
        )

        features = context.get(
            "features",
            []
        )

        contributor_stats = {}

        # ---------------------------------------------
        # INITIALIZE CONTRIBUTORS
        # ---------------------------------------------

        for contributor in contributors:

            name = contributor.get(
                "name",
                "Unknown"
            )

            contributor_stats[name] = {

                "developer":
                    name,

                "commits":
                    0,

                "assigned_features":
                    [],

                "actual_features":
                    [],

                "ownership_confidence":
                    0,

                "workload_hours":
                    0,

                "status":
                    "Active",

                "ownership_drift":
                    False
            }

        # ---------------------------------------------
        # COMMIT OWNERSHIP ANALYSIS
        # ---------------------------------------------

        for item in activity:

            author = item.get(
                "author"
            )

            if author in contributor_stats:

                contributor_stats[
                    author
                ]["commits"] += 1

        # ---------------------------------------------
        # FEATURE ASSIGNMENT ANALYSIS
        # ---------------------------------------------

        for feature in features:

            assigned = feature.get(
                "assigned_developers",
                []
            )

            expected_hours = feature.get(
                "expected_hours",
                0
            )

            feature_name = feature.get(
                "feature_name"
            )

            for dev in assigned:

                if dev in contributor_stats:

                    contributor_stats[
                        dev
                    ][
                        "assigned_features"
                    ].append(
                        feature_name
                    )

                    contributor_stats[
                        dev
                    ][
                        "workload_hours"
                    ] += expected_hours

        # ---------------------------------------------
        # OWNERSHIP CONFIDENCE
        # ---------------------------------------------

        total_commits = sum(

            contributor_stats[dev][
                "commits"
            ]

            for dev in contributor_stats
        )

        if total_commits <= 0:

            total_commits = 1

        for dev in contributor_stats:

            commits = contributor_stats[
                dev
            ][
                "commits"
            ]

            confidence = int(

                (commits / total_commits)
                * 100
            )

            contributor_stats[
                dev
            ][
                "ownership_confidence"
            ] = min(
                confidence,
                95
            )

            # -----------------------------------------
            # INACTIVE STATUS
            # -----------------------------------------

            if commits == 0:

                contributor_stats[
                    dev
                ][
                    "status"
                ] = "Inactive"

            # -----------------------------------------
            # OWNERSHIP DRIFT
            # -----------------------------------------

            assigned_count = len(

                contributor_stats[
                    dev
                ][
                    "assigned_features"
                ]
            )

            if assigned_count > 0 and commits == 0:

                contributor_stats[
                    dev
                ][
                    "ownership_drift"
                ] = True

        return list(
            contributor_stats.values()
        )