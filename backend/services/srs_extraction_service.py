import json
from datetime import datetime
from backend.storage.repositories_extended import SRSRepository, PlatformFetchRepository, AuditComparisonRepository
from backend.services.normalization_service import NormalizationService
from backend.srs.extractor import SRSFeatureExtractor

class SRSExtractionService:
    """Parse and persist SRS document using existing parser."""

    def __init__(self):
        from backend.srs.parser import SRSParser
        self.parser = SRSParser()
        self.srs_repo = SRSRepository()

    def extract_and_store(self, file_path: str):
        # file_path points to the saved file on disk
        
        extracted_features = None
        result = None
        
        if file_path.lower().endswith(".xlsx"):
            from backend.srs.workbook_parser import WorkbookParser
            wp = WorkbookParser()
            wb_features = wp.parse(file_path)
            if wb_features:
                extracted_features = wb_features
                result = {
                    "raw_content": "[Excel Document - Parsed via WorkbookParser]",
                    "cleaned_lines": []
                }
                
        if not extracted_features:
            result = self.parser.parse(file_path=file_path)
            
            # Immediately run feature extraction
            extractor = SRSFeatureExtractor()
            extracted_features = extractor.extract_features(result["raw_content"])
        
        # Map source-specific terms to canonical entities
        canonical_features = []
        for idx, f in enumerate(extracted_features):
                module_name = f.get("milestone") or f.get("component") or "General"
                canonical_features.append({
                    "module": module_name,
                    "requirement": f.get("feature_name", f"Requirement {idx + 1}"),
                    "planned_hours": float(f.get("expected_hours") or 0.0),
                    "assigned_developer": f.get("assigned_developers")[0] if f.get("assigned_developers") else "Unassigned"
                })
            
        result["features"] = canonical_features

        # store raw file path and extracted JSON
        srs_entry = self.srs_repo.save(
            uploaded_at=datetime.utcnow(),
            raw_file_path=file_path,
            extracted_json=result
        )
        return srs_entry
