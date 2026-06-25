import os
import sys
import pandas as pd
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.resource_mapping_service import ResourceMappingService
from backend.srs.workbook_parser import WorkbookParser

def test_resource_mapping():
    assert ResourceMappingService.map_resource("S1") == "S1 (Junior Developer)"
    assert ResourceMappingService.map_resource("A2") == "A2 (Mid-Level Developer)"
    assert ResourceMappingService.map_resource("s3") == "S3 (Senior Developer)"
    assert ResourceMappingService.map_resource("unknown") == "unknown"
    assert ResourceMappingService.map_resource("") == "Unassigned"

def test_workbook_parsing():
    df = pd.DataFrame({
        "Module": ["Auth", "Payments"],
        "Feature": ["Login", "Checkout"],
        "Estimated Hours": [10, 20.5],
        "Resource": ["S1", "A3"]
    })
    
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    tmp.close()
    tmp_path = tmp.name
        
    try:
        df.to_excel(tmp_path, index=False)
        
        parser = WorkbookParser()
        features = parser.parse(tmp_path)
        
        assert features is not None
        assert len(features) == 2
        
        assert features[0]["feature_name"] == "Login"
        assert features[0]["expected_hours"] == 10.0
        assert features[0]["assigned_developers"] == ["S1 (Junior Developer)"]
        assert features[0]["milestone"] == "Auth"
        
        assert features[1]["feature_name"] == "Checkout"
        assert features[1]["expected_hours"] == 20.5
        assert features[1]["assigned_developers"] == ["A3 (Senior Developer)"]
        assert features[1]["milestone"] == "Payments"
        
        print("SUCCESS: test_workbook_parsing passed.")
    finally:
        os.remove(tmp_path)

if __name__ == "__main__":
    test_resource_mapping()
    test_workbook_parsing()
