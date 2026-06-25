class ExecutiveReportEngine:

    # -------------------------------------------------
    # GENERATE REPORT
    # -------------------------------------------------

    def generate_report(

        self,
        profile
    ):

        report = {

            "summary":
                self._build_summary(
                    profile
                ),

            "key_findings":
                self._build_findings(
                    profile
                ),

            "recommendations":
                self._build_recommendations(
                    profile
                )
        }

        return report

    def _build_summary(

        self,
        profile
    ):

        return {

            "repository":
                profile["repository"],

            "workflow_style":
                profile["workflow_style"],

            "engineering_maturity":
                profile[
                    "engineering_maturity"
                ],

            "delivery_risk":
                profile[
                    "delivery_risk"
                ]
        }

    def _build_findings(

        self,
        profile
    ):

        findings = []

        if profile[
            "engineering_maturity"
        ] == "low":

            findings.append(

                "Engineering maturity is currently low."
            )

        if profile[
            "delivery_risk"
        ] != "normal":

            findings.append(

                "Delivery risk detected."
            )

        return findings

    def _build_recommendations(

        self,
        profile
    ):

        recommendations = []

        if profile[
            "workflow_style"
        ] == "commit_driven":

            recommendations.append(

                "Adopt PR-driven workflows."
            )

        if profile[
            "engineering_maturity"
        ] == "low":

            recommendations.append(

                "Introduce release engineering standards."
            )

        return recommendations