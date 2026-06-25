class PredictiveRiskEngine:

    def analyze(

        self,

        implementation_results,

        contributor_results,

        drift_results
    ):

        risks = []

        # -----------------------------------
        # IMPLEMENTATION RISKS
        # -----------------------------------

        for item in implementation_results:

            confidence = item.get(
                "confidence",
                0
            )

            requirement = item.get(
                "requirement",
                "Unknown"
            )

            if confidence < 50:

                risks.append({

                    "type":
                        "Implementation Risk",

                    "severity":
                        "HIGH",

                    "message":
                        f"{requirement} implementation confidence is critically low.",

                    "probability":
                        82
                })

            elif confidence < 75:

                risks.append({

                    "type":
                        "Implementation Risk",

                    "severity":
                        "MEDIUM",

                    "message":
                        f"{requirement} implementation is only partially complete.",

                    "probability":
                        61
                })

        # -----------------------------------
        # CONTRIBUTOR RISKS
        # -----------------------------------

        for contributor in contributor_results:

            commits = contributor.get(
                "commits",
                0
            )

            developer = contributor.get(
                "developer",
                "Unknown"
            )

            if commits > 500:

                risks.append({

                    "type":
                        "Burnout Risk",

                    "severity":
                        "MEDIUM",

                    "message":
                        f"{developer} may be overloaded with excessive ownership.",

                    "probability":
                        71
                })

        # -----------------------------------
        # ARCHITECTURAL DRIFT
        # -----------------------------------

        for drift in drift_results:

            risks.append({

                "type":
                    "Architecture Risk",

                "severity":
                    drift.get(
                        "severity",
                        "LOW"
                    ),

                "message":
                    drift.get(
                        "message",
                        "Unknown drift detected."
                    ),

                "probability":
                    76
            })

        return risks