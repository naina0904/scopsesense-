def risk_distribution_from_audit(

    latest
):

    risks = (

        latest.get(
            "predictive_risks",
            []
        )
        + latest.get(
            "hotspots",
            []
        )
    )

    high = 0
    medium = 0
    low = 0

    for risk in risks:

        level = (

            risk.get(
                "severity"
            )
            or risk.get(
                "risk_level"
            )
            or "low"
        ).lower()

        if level in [
            "high",
            "critical"
        ]:

            high += 1

        elif level in [
            "medium",
            "moderate"
        ]:

            medium += 1

        else:

            low += 1

    return {

        "high_risk":
            high,

        "medium_risk":
            medium,

        "low_risk":
            low
    }


def roadmap_from_audit(

    latest
):

    roadmap = []

    for item in latest.get(
        "recommendations",
        []
    ):

        roadmap.append({

            "project":
                latest.get(
                    "repository",
                    "Current Audit"
                ),

            "priority":
                item.get(
                    "priority",
                    "MEDIUM"
                ),

            "recommended_action":
                item.get(
                    "recommendation",
                    ""
                )
        })

    for item in (

        latest.get(
            "agent_findings",
            {}
        )
        .get(
            "planning",
            []
        )
    ):

        roadmap.append({

            "project":
                latest.get(
                    "repository",
                    "Current Audit"
                ),

            "priority":
                item.get(
                    "priority",
                    "MEDIUM"
                ),

            "recommended_action":
                item.get(
                    "task",
                    ""
                )
        })

    return roadmap
