from pydantic import BaseModel, Field
from typing import List, Optional
import json
import re

CATEGORY_SOFTWARE_FEATURE = "SOFTWARE_FEATURE"
CATEGORY_FUNCTIONAL_REQUIREMENT = "FUNCTIONAL_REQUIREMENT"
CATEGORY_NON_FUNCTIONAL_REQUIREMENT = "NON_FUNCTIONAL_REQUIREMENT"
CATEGORY_TIMELINE = "TIMELINE"
CATEGORY_TEAM_STRUCTURE = "TEAM_STRUCTURE"
CATEGORY_TECHNOLOGY = "TECHNOLOGY"
CATEGORY_NOISE = "NOISE"

ALL_CLASSIFICATION_CATEGORIES = [
    CATEGORY_SOFTWARE_FEATURE,
    CATEGORY_FUNCTIONAL_REQUIREMENT,
    CATEGORY_NON_FUNCTIONAL_REQUIREMENT,
    CATEGORY_TIMELINE,
    CATEGORY_TEAM_STRUCTURE,
    CATEGORY_TECHNOLOGY,
    CATEGORY_NOISE,
]

TIMELINE_TERMS = [
    "timeline",
    "schedule",
    "delivery",
    "milestone",
    "duration",
    "due",
    "deadline",
    "start date",
    "completion",
    "end date",
    "week",
    "day",
]
TEAM_TERMS = [
    "team",
    "teams",
    "organization",
    "org",
    "staff",
    "staffing",
    "roles",
    "responsibilities",
    "recommended team",
]
TECH_TERMS = [
    "technology",
    "technologies",
    "tech stack",
    "platform",
    "framework",
    "infrastructure",
    "architecture",
    "integration",
    "api",
    "sdk",
    "database",
    "cloud",
    "tools",
]
NFR_TERMS = [
    "performance",
    "security",
    "reliability",
    "availability",
    "scalability",
    "usability",
    "maintainability",
    "privacy",
    "compliance",
    "non-functional",
    "nfr",
    "quality",
]
FUNCTIONAL_TERMS = [
    "requirement",
    "requirements",
    "feature",
    "capability",
    "support",
    "provide",
    "allow",
    "should",
    "must",
]
NOISE_TERMS = [
    "summary",
    "overview",
    "introduction",
    "background",
    "notes",
    "details",
    "section",
    "deliverable",
    "recommendation",
    "decision",
    "documentation",
]


class SRSFeature(BaseModel):
    feature_id: str = Field(description="Unique identifier, e.g., FT-1, FT-2")
    feature_name: str = Field(description="Name of the software feature, module, or page")
    expected_hours: float = Field(default=0.0, description="Estimated effort hours")
    assigned_developers: List[str] = Field(default_factory=list, description="List of developers assigned")
    priority: str = Field(default="Medium", description="High, Medium, or Low")
    timeline: Optional[str] = Field(default=None, description="Timeline details or dates")
    dependencies: List[str] = Field(default_factory=list, description="Features this feature depends on")
    milestone: Optional[str] = Field(default=None, description="Milestone name or ID")


from backend.llm.manager import LLMManager


class SRSFeatureExtractor:

    def __init__(
        self,
        llm_manager=None
    ):
        self.llm_manager = llm_manager
        self.last_llm_error = None
        self.last_llm_provider_attempts = None
        self.debug_info = {
            "requested_provider": None,
            "successful_provider": None,
            "fallback_extraction_used": False,
            "raw_feature_names_before_normalization": [],
            "classification": {
                "category_counts": {cat: 0 for cat in ALL_CLASSIFICATION_CATEGORIES},
                "kept_count": 0,
                "filtered_count": 0,
                "sample_classifications": []
            }
        }

    def _clean_llm_json(self, text: str) -> str:
        text = text.strip()
        # Remove markdown code block markers if present
        if text.startswith("```"):
            newline_idx = text.find("\n")
            if newline_idx != -1:
                text = text[newline_idx:].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        return text

    def _classify_feature(self, feature: dict) -> str:
        if not isinstance(feature, dict):
            return CATEGORY_NOISE

        name = (feature.get("feature_name") or "").strip().lower()
        description = (feature.get("description") or "").strip().lower()
        text = f"{name} {description}"

        if any(term in text for term in TIMELINE_TERMS):
            return CATEGORY_TIMELINE
        if any(term in text for term in TEAM_TERMS):
            return CATEGORY_TEAM_STRUCTURE
        if any(term in text for term in TECH_TERMS):
            return CATEGORY_TECHNOLOGY
        if any(term in text for term in NFR_TERMS):
            return CATEGORY_NON_FUNCTIONAL_REQUIREMENT
        if any(term in name.split() for term in FUNCTIONAL_TERMS):
            return CATEGORY_FUNCTIONAL_REQUIREMENT
        if any(term in text for term in NOISE_TERMS):
            return CATEGORY_NOISE
        return CATEGORY_SOFTWARE_FEATURE

    def _apply_classification_metrics(self, features: list):
        category_counts = {cat: 0 for cat in ALL_CLASSIFICATION_CATEGORIES}
        sample_classifications = []

        for idx, feature in enumerate(features):
            category = self._classify_feature(feature)
            category_counts[category] = category_counts.get(category, 0) + 1
            if idx < 10:
                sample_classifications.append(
                    {
                        "feature_name": feature.get("feature_name"),
                        "category": category,
                        "description": feature.get("description")
                    }
                )

        kept_count = category_counts[CATEGORY_SOFTWARE_FEATURE]
        filtered_count = len(features) - kept_count

        self.debug_info["classification"] = {
            "category_counts": category_counts,
            "kept_count": kept_count,
            "filtered_count": filtered_count,
            "sample_classifications": sample_classifications,
        }

        return features

    # =================================================
    # EXTRACT FEATURES
    # =================================================

    def extract_features(
        self,
        content: str
    ):
        # Route to AI‑backed semantic parser for format‑agnostic extraction
        try:
            # Determine provider from the injected manager or default
            llm = self.llm_manager or LLMManager()
            self.debug_info = {
                "requested_provider": getattr(llm, "provider", None),
                "successful_provider": None,
                "provider_used": None,
                "provider_fallbacks": [],
                "provider_latency_ms": {},
                "fallback_extraction_used": False,
                "raw_feature_names_before_normalization": []
            }
            
            # Truncate the SRS content to stay within token budget before sending to LLM
            from backend.llm.token_budget import truncate_to_budget
            content = truncate_to_budget(content)
            prompt = f"""
You are an expert systems analyst and enterprise technical architect.
Your task is to analyze the provided SRS (Software Requirements Specification) document text, which may be parsed from a spreadsheet table, markdown, DOCX, or PDF, and extract all key software features, modules, and estimated timelines.

Convert the document into a structured JSON array representing the features.

For each feature, populate the following schema:
- "feature_id": String (e.g. "FT-1", "FT-2", "FT-3")
- "feature_name": String (Name of the software feature/module/page)
- "expected_hours": Float (Estimated development/effort hours. If days are provided like 14d, convert to hours assuming 8 hours per day, i.e., 14 * 8 = 112)
- "assigned_developers": Array of Strings (Developer names assigned to the feature, if any)
- "priority": String ("High", "Medium", "Low", default is "Medium")
- "timeline": String (Delivery timeline, e.g. "W1-W2", "Duration: 14 days", or null)
- "dependencies": Array of Strings (List of names of other features this feature depends on)
- "milestone": String (Associated milestone name or ID, or null)

CRITICAL: Return ONLY a valid JSON array. Do not include any conversational preamble, explanation, or markdown formatting outside the JSON itself.

SRS Content to extract:
---
{content}
---
"""
            print("[SRSFeatureExtractor] Initiating semantic AI requirement extraction...")
            try:
                raw_response = llm.generate(prompt)
                self.debug_info["successful_provider"] = getattr(llm, "last_successful_provider", getattr(llm, "provider", None))
                self.debug_info["provider_used"] = getattr(llm, "provider_used", getattr(llm, "last_successful_provider", None))
                self.debug_info["provider_fallbacks"] = getattr(llm, "provider_fallbacks", [])
                self.debug_info["provider_latency_ms"] = getattr(llm, "provider_latency_ms", {})
            except Exception as e:
                # capture provider-level errors for observability
                try:
                    self.last_llm_error = str(e)
                    self.last_llm_provider_attempts = getattr(e, 'attempts', None)
                except Exception:
                    self.last_llm_error = str(e)
                    self.last_llm_provider_attempts = None
                self.debug_info["fallback_extraction_used"] = True
                self.debug_info["provider_used"] = None
                self.debug_info["provider_fallbacks"] = getattr(llm, "provider_fallbacks", [])
                self.debug_info["provider_latency_ms"] = getattr(llm, "provider_latency_ms", {})
                print(f"[SRSFeatureExtractor] AI-backed extraction failed: {e}. Falling back to default parser.")
                raise
            cleaned_response = self._clean_llm_json(raw_response)
            
            extracted_data = json.loads(cleaned_response)
            if isinstance(extracted_data, list):
                normalized_features = []
                for idx, item in enumerate(extracted_data):
                    if not isinstance(item, dict):
                        continue
                    
                    # Normalize alternative names before pydantic validation
                    raw_name = item.get("feature_name") or item.get("name") or "Unnamed Feature"
                    if len(self.debug_info["raw_feature_names_before_normalization"]) < 5:
                        self.debug_info["raw_feature_names_before_normalization"].append(raw_name)
                    f_name = raw_name.replace("\t", " ").strip()
                    
                    try:
                        hours = float(item.get("expected_hours", 0.0) or item.get("hours", 0.0))
                    except (ValueError, TypeError):
                        hours = 0.0
                        
                    devs = item.get("assigned_developers") or item.get("developers") or []
                    if isinstance(devs, str):
                        devs = [d.strip() for d in devs.split(",") if d.strip()]
                        
                    deps = item.get("dependencies") or []
                    if isinstance(deps, str):
                        deps = [d.strip() for d in deps.split(",") if d.strip()]

                    # Construct and validate using Pydantic
                    feature_obj = SRSFeature(
                        feature_id=item.get("feature_id") or f"FT-{idx+1}",
                        feature_name=f_name,
                        expected_hours=hours,
                        assigned_developers=devs,
                        priority=item.get("priority") or "Medium",
                        timeline=item.get("timeline") or None,
                        dependencies=deps,
                        milestone=item.get("milestone") or None
                    )
                    
                    normalized_features.append(feature_obj.model_dump())
                
                if normalized_features:
                    print(f"[SRSFeatureExtractor] Semantically extracted {len(normalized_features)} features using AI.")
                    return self._apply_classification_metrics(normalized_features)
        except Exception as e:
            print(f"[SRSFeatureExtractor] AI-backed extraction failed: {e}. Falling back to default parser.")

        # Default legacy parser for testing and fallback scenarios
        features = []
        blocks = content.split("Feature:")

        for idx, block in enumerate(blocks):
            block = block.strip()
            if not block:
                continue

            # The first block (idx==0) is always the text BEFORE the first "Feature:" marker
            if idx == 0:
                continue

            lines = [line.strip() for line in block.split("\n") if line.strip()]
            raw_name = lines[0]
            if len(self.debug_info["raw_feature_names_before_normalization"]) < 5:
                self.debug_info["raw_feature_names_before_normalization"].append(raw_name)
            self.debug_info["fallback_extraction_used"] = True
            feature_data = {
                "feature_id": f"FT-{idx}",
                "feature_name": raw_name,
                "expected_hours": 0.0,
                "assigned_developers": [],
                "priority": "Medium",
                "timeline": None,
                "dependencies": [],
                "milestone": None
            }

            # Field parsing
            for line in lines[1:]:
                if line.startswith("Hours:"):
                    try:
                        feature_data["expected_hours"] = float(line.replace("Hours:", "").strip())
                    except ValueError:
                        feature_data["expected_hours"] = 0.0

                elif line.startswith("Timeline:"):
                    raw_timeline = line.replace("Timeline:", "").strip()
                    feature_data["timeline"] = raw_timeline

                    # Auto-convert duration strings to hours
                    day_match = re.match(r"^(\d+(?:\.\d+)?)d$", raw_timeline, re.IGNORECASE)
                    week_match = re.match(r"^(\d+(?:\.\d+)?)w$", raw_timeline, re.IGNORECASE)
                    hour_match = re.match(r"^(\d+(?:\.\d+)?)h$", raw_timeline, re.IGNORECASE)

                    if day_match:
                        feature_data["expected_hours"] = float(day_match.group(1)) * 8.0
                    elif week_match:
                        feature_data["expected_hours"] = float(week_match.group(1)) * 40.0
                    elif hour_match:
                        feature_data["expected_hours"] = float(hour_match.group(1))

                elif line.startswith("Developers:"):
                    developers = line.replace("Developers:", "").strip().split(",")
                    feature_data["assigned_developers"] = [dev.strip() for dev in developers if dev.strip()]

                elif line.startswith("Priority:"):
                    feature_data["priority"] = line.replace("Priority:", "").strip()

                elif line.startswith("Dependencies:"):
                    dependencies = line.replace("Dependencies:", "").strip().split(",")
                    feature_data["dependencies"] = [dep.strip() for dep in dependencies if dep.strip()]

                elif line.startswith("Milestone:"):
                    feature_data["milestone"] = line.replace("Milestone:", "").strip()

            # Validate fallback parser output with Pydantic
            try:
                validated_feature = SRSFeature(**feature_data)
                features.append(validated_feature.model_dump())
            except Exception as parse_err:
                print(f"[SRSFeatureExtractor] Fallback parsing validation failed for feature block {idx}: {parse_err}")
                features.append(feature_data)

        # If no features were found using explicit "Feature:" markers,
        # attempt a richer, heuristic-based extraction that handles
        # XLSX-derived markdown tables, requirement sections, module lists,
        # and capability lists.
        if not features:
            try:
                heur_features = self._fallback_heuristic_extract(content)
                if heur_features:
                    self.debug_info["fallback_extraction_used"] = True
                    for feat in heur_features:
                        if len(self.debug_info["raw_feature_names_before_normalization"]) < 5:
                            self.debug_info["raw_feature_names_before_normalization"].append(feat.get("feature_name", "Unnamed Feature"))
                    print(f"[SRSFeatureExtractor] Heuristic fallback extracted {len(heur_features)} features.")
                    return self._apply_classification_metrics(heur_features)
            except Exception as hf_err:
                print(f"[SRSFeatureExtractor] Heuristic fallback failed: {hf_err}")

        return self._apply_classification_metrics(features)

    # =================================================
    # Heuristic fallback parsers
    # =================================================

    def _parse_markdown_tables(self, text: str):
        """Parse simple markdown tables and return a list of tables (each is a list of row dicts/lists)."""
        tables = []
        current_table = []
        lines = text.splitlines()

        for line in lines:
            if line.strip().startswith("|"):
                current_table.append(line.strip())
            else:
                if current_table:
                    tables.append(current_table)
                    current_table = []
                    
        if current_table:
            tables.append(current_table)

        parsed_tables = []
        for tbl in tables:
            rows = []
            for r in tbl:
                if re.match(r"^\|\s*-{2,}", r):
                    continue
                cells = [c.strip() for c in r.strip().strip("|").split("|")]
                rows.append(cells)
            if rows:
                parsed_tables.append(rows)

        return parsed_tables

    def _extract_items_from_paragraph(self, para: str):
        """Extract candidate feature names from a paragraph using commas and 'and'."""
        items = []
        # Find bullet-like sections first
        for line in para.splitlines():
            s = line.strip()
            if s.startswith(('-', '*', '+')):
                candidate = s.lstrip('-*+').strip()
                if candidate:
                    items.append(candidate)

        if items:
            return items

        # fallback: split by commas/and
        parts = re.split(r",| and |;", para)
        for p in parts:
            p = p.strip()
            # filter out very short or generic fragments
            if len(p) >= 4 and not p.lower().startswith('the '):
                items.append(p)

        return items

    def _fallback_heuristic_extract(self, content: str):
        """Try multiple heuristics to extract features when explicit markers are absent."""
        features_dict = {}
        module_hours = {}

        # 1) Parse markdown tables for delivery timeline
        tables = self._parse_markdown_tables(content)
        for table in tables:
            if not table:
                continue
            header_idx = -1
            for i, row in enumerate(table):
                headers = [str(h).lower() for h in row]
                if any("dev days" in h or "testing days" in h for h in headers) and any("module" in h for h in headers):
                    header_idx = i
                    break
                    
            if header_idx >= 0:
                headers = [str(h).lower() for h in table[header_idx]]
                try:
                    mod_idx = headers.index(next(h for h in headers if "module" in h))
                    dev_idx = headers.index(next(h for h in headers if "dev days" in h))
                except StopIteration:
                    continue
                for row in table[header_idx + 1:]:
                    if len(row) > max(mod_idx, dev_idx):
                        mod_name = row[mod_idx].strip()
                        dev_days_str = row[dev_idx].strip()
                        m = re.match(r"(\d+(?:\.\d+)?)", dev_days_str)
                        if m and mod_name:
                            module_hours[mod_name.lower()] = float(m.group(1)) * 8.0

        # 2) Parse the "MODULE_NAME: ... Features: ... \ufffd Feature Name: Desc" structure
        current_module = "General"
        lines = content.splitlines()
        in_features_block = False
        
        for line in lines:
            s_line = line.strip()
            if not s_line:
                continue

            # Check if this line is a module header: ALL CAPS + ":" or "Module:"
            mod_match = re.match(r"^([A-Z0-9\s&_]+):\s*(.*)", s_line)
            if mod_match and len(mod_match.group(1).split()) <= 6:
                possible_mod = mod_match.group(1).strip()
                if possible_mod.lower() not in ["features", "requirements", "note", "notes", "important"]:
                    current_module = possible_mod.title()
                    in_features_block = False
                    continue
                
            if "Features:" in s_line or "Requirements:" in s_line:
                in_features_block = True
                continue
                
            if in_features_block:
                # Match bullet points: \ufffd, -, *, \u2022
                feat_match = re.match(r"^[\ufffd\-\*\+\u2022]\s*(.*?):\s*(.*)", s_line)
                if feat_match:
                    f_name = feat_match.group(1).strip()
                    if len(f_name) < 3 or f_name.lower() in ("document title", "introduction"):
                        continue
                        
                    key = f_name.lower()
                    if key not in features_dict:
                        features_dict[key] = {
                            "feature_id": f"FT-H-{len(features_dict) + 1}",
                            "feature_name": f_name,
                            "expected_hours": 0.0,
                            "assigned_developers": [],
                            "priority": "Medium",
                            "timeline": None,
                            "dependencies": [],
                            "milestone": current_module,
                        }

        # 3) Map module hours to features evenly
        mod_feature_keys = {}
        for k, v in features_dict.items():
            mod = v["milestone"].lower()
            if mod not in mod_feature_keys:
                mod_feature_keys[mod] = []
            mod_feature_keys[mod].append(k)
            
        for mod, f_keys in mod_feature_keys.items():
            if mod in module_hours and len(f_keys) > 0:
                total_hours = module_hours[mod]
                hours_per_feat = round(total_hours / len(f_keys), 1)
                for k in f_keys:
                    features_dict[k]["expected_hours"] = hours_per_feat

        features = []
        for key, fd in features_dict.items():
            try:
                vf = SRSFeature(**fd)
                features.append(vf.model_dump())
            except Exception:
                features.append(fd)
                
        return features
