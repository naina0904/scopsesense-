class PlanningAgent:

    def __init__(
        self,
        llm_manager=None
    ):
        self.llm_manager = llm_manager

    def generate_plan(

        self,

        predictive_risks,

        recommendations,

        architecture_scores
    ):

        roadmap = []

        # -----------------------------------
        # HIGH PRIORITY RISKS
        # -----------------------------------

        for risk in predictive_risks:

            severity = risk.get(
                "severity",
                "LOW"
            )

            message = risk.get(
                "message",
                ""
            )

            if severity == "HIGH":

                roadmap.append({

                    "phase":
                        "Immediate",

                    "priority":
                        "HIGH",

                    "task":
                        f"Resolve critical risk: {message}"
                })

        # -----------------------------------
        # ARCHITECTURE
        # -----------------------------------

        stability = (
            architecture_scores.get(
                "stability_score",
                100
            )
        )

        if stability < 70:

            roadmap.append({

                "phase":
                    "Short Term",

                "priority":
                    "HIGH",

                "task":
                    "Improve infrastructure stability and reduce dependency bottlenecks."
            })

        # -----------------------------------
        # RECOMMENDATIONS
        # -----------------------------------

        for recommendation in recommendations:

            roadmap.append({

                "phase":
                    "Planned",

                "priority":
                    recommendation.get(
                        "priority",
                        "MEDIUM"
                    ),

                "task":
                    recommendation.get(
                        "recommendation",
                        ""
                    )
            })

        return roadmap