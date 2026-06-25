class RiskEngine:

    # -------------------------------------------------
    # ANALYZE RISKS
    # -------------------------------------------------

    def analyze_risks(

        self,
        profile
    ):

        risks = {

            "bus_factor":
                self._detect_bus_factor(
                    profile
                ),

            "pr_congestion":
                self._detect_pr_congestion(
                    profile
                ),

            "review_overload":
                self._detect_review_overload(
                    profile
                ),

            "release_risk":
                self._detect_release_risk(
                    profile
                ),

            "execution_fragility":
                self._detect_execution_fragility(
                    profile
                )
        }

        risks[
            "overall_risk"
        ] = self._calculate_overall_risk(
            risks
        )

        return risks

    def _detect_bus_factor(

        self,
        profile
    ):

        contributors = profile[
            "contributors"
        ][
            "contributors"
        ]

        if len(contributors) <= 1:

            return {

                "risk":
                    "critical",

                "message":
                    "Single contributor dependency"
            }

        return {

            "risk":
                "healthy"
        }

    def _detect_pr_congestion(

        self,
        profile
    ):

        open_prs = profile[
            "pull_requests"
        ][
            "summary"
        ][
            "open_prs"
        ]

        if open_prs > 20:

            return {

                "risk":
                    "critical"
            }

        return {

            "risk":
                "healthy"
        }

    def _detect_review_overload(

        self,
        profile
    ):

        oversized = profile[
            "pull_requests"
        ][
            "summary"
        ][
            "oversized_prs"
        ]

        if oversized > 10:

            return {

                "risk":
                    "critical"
            }

        return {

            "risk":
                "healthy"
        }

    def _detect_release_risk(

        self,
        profile
    ):

        releases = profile[
            "releases"
        ][
            "release_count"
        ]

        if releases == 0:

            return {

                "risk":
                    "moderate",

                "message":
                    "No formal releases detected"
            }

        return {

            "risk":
                "healthy"
        }

    def _detect_execution_fragility(

        self,
        profile
    ):

        branches = profile[
            "branches"
        ][
            "total_branches"
        ]

        if branches <= 1:

            return {

                "risk":
                    "critical"
            }

        return {

            "risk":
                "healthy"
        }

    def _calculate_overall_risk(

        self,
        risks
    ):

        critical = 0

        for value in risks.values():

            if (
                isinstance(
                    value,
                    dict
                )
                and value.get(
                    "risk"
                ) == "critical"
            ):

                critical += 1

        if critical >= 3:

            return "critical"

        if critical >= 1:

            return "moderate"

        return "healthy"