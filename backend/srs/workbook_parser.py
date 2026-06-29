import pandas as pd
from typing import List, Dict, Optional, Any
from backend.services.resource_mapping_service import ResourceMappingService

class WorkbookParser:
    """Heuristic parser for Excel planning workbooks using Pandas."""
    
    # Common column aliases for mapping
    MODULE_ALIASES = ["module", "component", "area", "epic", "category"]
    FEATURE_ALIASES = ["feature", "requirement", "task", "name", "capability", "description"]
    HOURS_ALIASES = ["estimated hours", "effort", "hours", "expected hours", "planned hours", "estimate"]
    RESOURCE_ALIASES = ["resource", "developer", "assignee", "owner", "role"]
    SL_ALIASES = ["sl", "s.l", "s.l.", "serial no", "serial number", "no.", "s.no"]

    def _normalize_header(self, col: Any) -> str:
        return str(col).strip().lower()

    def _find_column(self, headers: List[str], aliases: List[str]) -> Optional[str]:
        for header in headers:
            norm_head = self._normalize_header(header)
            for alias in aliases:
                if alias in norm_head:
                    return header
        return None

    def _score_header(self, row_vals: List[str]) -> int:
        score = 0
        has_sl = False
        has_module = False
        has_feature = False
        has_hours = False
        has_developer = False
        
        for val in row_vals:
            norm = self._normalize_header(val)
            if norm in ["sl", "s.l", "s.l.", "serial no", "serial number", "no.", "s.no"]:
                has_sl = True
            if any(x in norm for x in ["module", "epic", "category", "area", "component"]):
                has_module = True
            if any(x in norm for x in ["feature", "requirement", "task", "description"]):
                has_feature = True
            if any(x in norm for x in ["hours", "effort", "estimate", "planned"]):
                has_hours = True
            if any(x in norm for x in ["developer", "resource", "assignee", "role", "s1", "s2", "s3"]):
                has_developer = True
                
        if has_sl: score += 1
        if has_module: score += 2
        if has_feature: score += 2
        if has_hours: score += 2
        if has_developer: score += 1
        
        return score

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Finds the row index that looks most like a header row."""
        best_row_idx = -1
        max_score = 0
        
        # Check column names first (row -1 conceptually)
        headers = [str(c) for c in df.columns]
        score = self._score_header(headers)
        if score >= 5:
            return -1 # means the df.columns are the headers
            
        # Check first 50 rows
        for i in range(min(50, len(df))):
            row_vals = [str(x) for x in df.iloc[i].values if pd.notna(x)]
            score = self._score_header(row_vals)
            if score > max_score:
                max_score = score
                best_row_idx = i
                
        if max_score >= 5:
            return best_row_idx
            
        return None

    def parse(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Attempt to parse the Excel file heuristically.
        Returns a list of extracted features, or None if ambiguous/failed.
        """
        try:
            features = []
            
            with pd.ExcelFile(file_path) as xls:
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    
                    if df.empty or len(df.columns) < 2:
                        continue
                        
                    header_idx = self._find_header_row(df)
                    if header_idx is None:
                        continue
                        
                    if header_idx > -1:
                        # Promote the found row to header
                        df.columns = df.iloc[header_idx].values
                        df = df.iloc[header_idx+1:].reset_index(drop=True)
                    
                    headers = [str(c) for c in df.columns]
                    
                    module_col = self._find_column(headers, self.MODULE_ALIASES)
                    feature_col = self._find_column(headers, self.FEATURE_ALIASES)
                    hours_col = self._find_column(headers, self.HOURS_ALIASES)
                    resource_col = self._find_column(headers, self.RESOURCE_ALIASES)
                    sl_col = self._find_column(headers, self.SL_ALIASES)
                    
                    # Must have at least feature and hours
                    if not feature_col or not hours_col:
                        continue
                    
                    current_module = "General"
                    total_accumulated_hours = 0.0
                    import re

                    for _, row in df.iterrows():
                        # Handle Feature
                        feature_val = str(row[feature_col]).strip()
                        if not feature_val or feature_val.lower() == "nan" or feature_val.lower() == "none":
                            continue
                            
                        # Handle Module (Downward Propagation)
                        has_explicit_module = False
                        if module_col and pd.notna(row[module_col]):
                            val = str(row[module_col]).strip()
                            if val.lower() not in ["nan", "none", ""]:
                                current_module = val
                                has_explicit_module = True
                                
                        # Handle Hours and Resource embedded parsing
                        hours_val = 0.0
                        resource_val = "Unassigned"
                        
                        if pd.notna(row[hours_col]):
                            val_str = str(row[hours_col]).strip()
                            embedded_match = re.search(r"([\d\.]+)\s*[\(\-\|]\s*([A-Za-z]\d)[\)]?", val_str)
                            if embedded_match:
                                hours_val = float(embedded_match.group(1))
                                res_code = embedded_match.group(2)
                                resource_val = ResourceMappingService.map_resource(res_code)
                            else:
                                try:
                                    if isinstance(row[hours_col], (int, float)):
                                        hours_val = float(row[hours_col])
                                    else:
                                        clean_val = val_str.lower().replace("h", "").replace("hrs", "").replace("hours", "")
                                        hours_val = float(clean_val)
                                except ValueError:
                                    hours_val = 0.0
                                    
                        norm_feat = feature_val.lower().strip()
                        if norm_feat in ["design and development", "design and deployment", "total estimated hours", "total"]:
                            print(f"[WorkbookParser] Ignoring summary header row: '{feature_val}'")
                            continue
                            
                        # Structural Global Phase Check
                        has_sl = sl_col and pd.notna(row[sl_col]) and str(row[sl_col]).strip().lower() not in ["nan", "none", ""]
                        if norm_feat in ["internal testing", "client testing", "deployment"] or (not has_explicit_module and not has_sl):
                            module_val = "Project Phases"
                        else:
                            module_val = current_module
                            
                        # Fallback for uncalculated formula values in known lifecycle phases
                        if hours_val == 0.0 and total_accumulated_hours > 0:
                            if "internal testing" in norm_feat:
                                hours_val = round(total_accumulated_hours * 0.2, 1)
                            elif "client testing" in norm_feat:
                                hours_val = round(total_accumulated_hours * 0.1, 1)
                            elif "deployment" in norm_feat:
                                hours_val = round(total_accumulated_hours * 0.1, 1)
                                
                        if module_val != "Project Phases":
                            total_accumulated_hours += hours_val
                            
                        # Handle separate Resource Column if embedded failed
                        if resource_val == "Unassigned" and resource_col and pd.notna(row[resource_col]):
                            raw_resource = str(row[resource_col]).strip()
                            if raw_resource.lower() not in ["nan", "none", ""]:
                                resource_val = ResourceMappingService.map_resource(raw_resource)
                                
                        if resource_val == "Unassigned":
                            if "internal testing" in norm_feat:
                                resource_val = "S2 (Mid-Level Developer)"
                            elif "client testing" in norm_feat or "deployment" in norm_feat:
                                resource_val = "S3 (Senior Developer)"
                                
                        feature_id = f"FT-XLS-{len(features) + 1}"
                        
                        features.append({
                            "feature_id": feature_id,
                            "feature_name": feature_val,
                            "expected_hours": hours_val,
                            "assigned_developers": [resource_val] if resource_val != "Unassigned" else [],
                            "priority": "Medium",
                            "milestone": module_val,
                            "dependencies": [],
                            "timeline": None
                        })
            
            if len(features) > 0:
                print(f"[WorkbookParser] Heuristically extracted {len(features)} features via Pandas.")
                return features
                
            return None
        except Exception as e:
            print(f"[WorkbookParser] Failed heuristic parse: {e}")
            return None
