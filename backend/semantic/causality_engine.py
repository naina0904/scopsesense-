class EngineeringCausalityEngine:

    # -------------------------------------------------
    # MAIN ANALYSIS
    # -------------------------------------------------

    def analyze(

        self,

        timeline_analysis,

        contributor_analysis,

        risk_analysis=None
    ):

        findings = []

        # ---------------------------------------------
        # TIMELINE DELAYS
        # ---------------------------------------------

        timeline_status = timeline_analysis.get(
            "status"
        )

        if timeline_status == "critical_delay":

            findings.append(
                "Critical execution delay detected"
            )

        elif timeline_status == "moderate_delay":

            findings.append(
                "Moderate delivery delay detected"
            )

        # ---------------------------------------------
        # CONTRIBUTOR ANALYSIS
        # ---------------------------------------------

        overloaded = []

        inactive = []

        ownership_drift = []

        for contributor in contributor_analysis:

            workload = contributor.get(
                "workload_hours",
                0
            )

            commits = contributor.get(
                "commits",
                0
            )

            if workload > 160:

                overloaded.append(
                    contributor["developer"]
                )

            if commits == 0:

                inactive.append(
                    contributor["developer"]
                )

            if contributor.get(
                "ownership_drift"
            ):

                ownership_drift.append(
                    contributor["developer"]
                )

        # ---------------------------------------------
        # OVERLOAD FINDINGS
        # ---------------------------------------------

        if overloaded:

            findings.append(

                "Contributor overload detected: "
                + ", ".join(overloaded)
            )

        # ---------------------------------------------
        # INACTIVE FINDINGS
        # ---------------------------------------------

        if inactive:

            findings.append(

                "Inactive assigned contributors: "
                + ", ".join(inactive)
            )

        # ---------------------------------------------
        # OWNERSHIP DRIFT
        # ---------------------------------------------

        if ownership_drift:

            findings.append(

                "Ownership drift detected: "
                + ", ".join(ownership_drift)
            )

        # ---------------------------------------------
        # RISK ANALYSIS
        # ---------------------------------------------

        if risk_analysis:

            risk_level = risk_analysis.get(
                "risk_level"
            )

            if risk_level == "high":

                findings.append(
                    "High architectural instability"
                )

        # ---------------------------------------------
        # FINAL STATUS
        # ---------------------------------------------

        overall_status = "healthy"

        if len(findings) >= 4:

            overall_status = "critical"

        elif len(findings) >= 2:

            overall_status = "moderate"

        return {

            "status":
                overall_status,

            "findings":
                findings
        }