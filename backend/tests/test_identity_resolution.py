import pytest
from backend.identity.identity_resolution_engine import IdentityResolutionEngine
from backend.core.audit_workflow import AuditWorkflow

def test_identity_resolution_suppression():
    # 1. Initialize IRE
    manual_aliases = {
        "Alice Smith": ["S2", "alice-smith99", "alice"]
    }
    ire = IdentityResolutionEngine(manual_aliases)

    # 2. Add source identities
    source_identities = [
        {"identity": "alice-smith99", "source": "GitHub"},
        {"identity": "Alice Smith", "source": "Jira"},
        {"identity": "S2", "source": "SRS"}
    ]

    # 3. Resolve identities
    identity_map = ire.resolve_identities(source_identities)
    
    # 4. Check if they are matched
    assert ire.are_same_person("S2", "alice-smith99", identity_map)
    assert ire.are_same_person("Alice Smith", "alice-smith99", identity_map)

    # 5. Create mock GitHub PlatformData feature mimicking Ghost Authorship
    class MockFeature:
        def __init__(self):
            self.assigned_to = "S2"
            self.active_contributors = ["alice-smith99"]
            self.variance_detected = True
            self.variance_reason = "Ghost Authorship detected: Unrecognized developer."
            self.name = "Mock Feature"

    class MockPlatformData:
        def __init__(self):
            self.features = [MockFeature()]
            self.contributors = []

    github_pdata = MockPlatformData()

    # 6. Apply IRE logic to suppress ghost authorship
    # (Extracting just the suppression logic from AuditWorkflow to test it)
    for feature in github_pdata.features:
        if feature.variance_detected and feature.variance_reason and "Ghost Authorship" in feature.variance_reason:
            assigned = feature.assigned_to
            authors = feature.active_contributors
            if assigned and authors:
                for author in authors:
                    if ire.are_same_person(assigned, author, identity_map):
                        feature.variance_detected = False
                        feature.variance_reason = ire.explain_resolution(assigned, author, identity_map)
                        break

    # 7. Assert ghost authorship flag was removed
    assert github_pdata.features[0].variance_detected == False
    assert "Ghost Authorship Suppressed" in github_pdata.features[0].variance_reason
    assert "Manual Alias Mapping" in github_pdata.features[0].variance_reason
