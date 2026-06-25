from backend.api.analytics_contracts import (
    risk_distribution_from_audit,
    roadmap_from_audit,
)


def test_analytics_risks_contract_from_semantic_payload():

    result = risk_distribution_from_audit({
        "predictive_risks": [
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
        ],
        "hotspots": [
            {"risk_level": "critical"},
            {"risk_level": "low"},
        ],
    })

    assert result == {
        "high_risk": 2,
        "medium_risk": 1,
        "low_risk": 1,
    }


def test_analytics_roadmap_contract_from_recommendations():

    result = roadmap_from_audit({
        "repository": "scopesense-v2",
        "recommendations": [
            {
                "priority": "HIGH",
                "recommendation": "Stabilize audit flow",
            }
        ],
        "agent_findings": {
            "planning": [
                {
                    "priority": "MEDIUM",
                    "task": "Add semantic regression tests",
                }
            ]
        },
    })

    assert result[0]["project"] == "scopesense-v2"
    assert result[0]["recommended_action"] == "Stabilize audit flow"
    assert result[1]["recommended_action"] == "Add semantic regression tests"
