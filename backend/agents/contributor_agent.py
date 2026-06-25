class ContributorAgent:

    def __init__(
        self,
        llm_manager=None
    ):
        self.llm_manager = llm_manager

    def analyze(

        self,

        contributors
    ):

        findings = []

        for contributor in contributors:

            commits = contributor.get(
                "commits",
                0
            )

            developer = contributor.get(
                "developer",
                "Unknown"
            )

            if commits > 500:

                findings.append(

                    f"{developer} has unusually high repository ownership."
                )

        return findings