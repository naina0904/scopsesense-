class ScoringEngine:

    # -------------------------------------------------
    # GENERATE SCORES
    # -------------------------------------------------

    def generate_scores(

        self,
        profile
    ):

        scores = {

            "engineering_health":

                self._engineering_health(
                    profile
                ),

            "delivery_health":

                self._delivery_health(
                    profile
                ),

            "collaboration_health":

                self._collaboration_health(
                    profile
                ),

            "release_maturity":

                self._release_maturity(
                    profile
                ),

            "risk_score":

                self._risk_score(
                    profile
                )
        }

        scores[
            "overall_score"
        ] = (

            self._overall_score(
                scores
            )
        )

        return scores

    # -------------------------------------------------
    # ENGINEERING HEALTH
    # -------------------------------------------------

    def _engineering_health(

        self,
        profile
    ):

        contributors = len(

            profile[
                "contributors"
            ][
                "contributors"
            ]
        )

        branches = profile[
            "branches"
        ][
            "total_branches"
        ]

        score = 50

        score += min(
            contributors * 5,
            25
        )

        score += min(
            branches * 2,
            25
        )

        return min(score, 100)

    # -------------------------------------------------
    # DELIVERY HEALTH
    # -------------------------------------------------

    def _delivery_health(

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

        oversized_prs = profile[
            "pull_requests"
        ][
            "summary"
        ][
            "oversized_prs"
        ]

        score = 100

        score -= open_prs * 2
        score -= oversized_prs * 3

        return max(score, 0)

    # -------------------------------------------------
    # COLLABORATION
    # -------------------------------------------------

    def _collaboration_health(

        self,
        profile
    ):

        contributors = len(

            profile[
                "contributors"
            ][
                "contributors"
            ]
        )

        if contributors >= 10:
            return 100

        if contributors >= 5:
            return 75

        if contributors >= 2:
            return 50

        return 20

    # -------------------------------------------------
    # RELEASE MATURITY
    # -------------------------------------------------

    def _release_maturity(

        self,
        profile
    ):

        releases = profile[
            "releases"
        ][
            "release_count"
        ]

        if releases >= 10:
            return 100

        if releases >= 5:
            return 75

        if releases >= 1:
            return 50

        return 10

    # -------------------------------------------------
    # RISK SCORE
    # -------------------------------------------------

    def _risk_score(

        self,
        profile
    ):

        overall_risk = (

            profile[
                "risk_analysis"
            ][
                "overall_risk"
            ]
        )

        if overall_risk == "healthy":
            return 90

        if overall_risk == "moderate":
            return 50

        return 20

    # -------------------------------------------------
    # OVERALL SCORE
    # -------------------------------------------------

    def _overall_score(

        self,
        scores
    ):

        total = sum(

            scores.values()
        )

        return round(
            total / len(scores),
            2
        )
    