class ArchitectureAgent:

    def __init__(
        self,
        llm_manager=None
    ):
        self.llm_manager = llm_manager

    def analyze(

        self,

        architecture_scores,

        dependencies
    ):

        findings = []

        # -----------------------------------
        # COUPLING
        # -----------------------------------

        coupling = (
            architecture_scores.get(
                "coupling_score",
                100
            )
        )

        if coupling < 70:

            findings.append(

                "High dependency coupling detected across repository modules."
            )

        # -----------------------------------
        # CIRCULAR
        # -----------------------------------

        if architecture_scores.get(
            "circular_dependency_risk"
        ):

            findings.append(

                "Circular dependency chains increase instability risk."
            )

        # -----------------------------------
        # LARGE DEPENDENCY CHAINS
        # -----------------------------------

        for item in dependencies:

            imports = item.get(
                "imports",
                []
            )

            if len(imports) > 10:

                findings.append(

                    f"{item['file']} contains excessive dependency imports."
                )

        return findings