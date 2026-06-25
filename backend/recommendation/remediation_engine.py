class RemediationEngine:

    def generate(

        self,

        predictive_risks,

        architecture_scores
    ):

        recommendations = []

        # -----------------------------------
        # ARCHITECTURE STABILITY
        # -----------------------------------

        stability_score = (
            architecture_scores.get(
                "stability_score",
                100
            )
        )

        if stability_score < 70:

            recommendations.append({

                "category":
                    "Architecture",

                "priority":
                    "HIGH",

                "recommendation":
                    "Improve system stability by reducing critical dependency chains and introducing infrastructure redundancy."
            })

        # -----------------------------------
        # CIRCULAR DEPENDENCIES
        # -----------------------------------

        if architecture_scores.get(
            "circular_dependency_risk"
        ):

            recommendations.append({

                "category":
                    "Architecture",

                "priority":
                    "HIGH",

                "recommendation":
                    "Refactor circular dependencies into isolated service abstractions."
            })

        # -----------------------------------
        # RISK-BASED RECOMMENDATIONS
        # -----------------------------------

        for risk in predictive_risks:

            message = risk.get(
                "message",
                ""
            ).lower()

            if "redis" in message:

                recommendations.append({

                    "category":
                        "Infrastructure",

                    "priority":
                        "HIGH",

                    "recommendation":
                        "Add Redis failover, retry policies, and connection pooling."
                })

            if "burnout" in message:

                recommendations.append({

                    "category":
                        "Engineering Management",

                    "priority":
                        "MEDIUM",

                    "recommendation":
                        "Redistribute repository ownership to reduce contributor overload."
                })

            if "implementation" in message:

                recommendations.append({

                    "category":
                        "Delivery",

                    "priority":
                        "HIGH",

                    "recommendation":
                        "Increase implementation coverage for incomplete requirements."
                })

        return recommendations