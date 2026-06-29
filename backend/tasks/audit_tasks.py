from backend.tasks.celery_app import (

    celery

)



from backend.services.audit_service import (

    AuditService

)



# =================================================

# SERVICES

# =================================================



audit_service = AuditService()



# =================================================

# EXECUTE AUDIT TASK

# =================================================



@celery.task(bind=True, max_retries=3, default_retry_delay=60)

def execute_audit(



    self,



    owner,



    repo,



    srs_path,



    provider="gemini"

):



    result = (



        audit_service

        .execute_full_audit(



            github_owner=

                owner,



            github_repo=

                repo,



            provider=
                provider,

            srs_path=
                srs_path,

            audit_run_id=
                self.request.id
        )
    )


    return result

# =================================================
# EXECUTE DELAY ANALYSIS TASK
# =================================================

from backend.observability.structured_logger import get_logger
from backend.storage.database import SessionLocal
from backend.storage.models_extended import AuditResult, FindingRecord

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def execute_delay_analysis_task(self, session_id: int, provider: str = "groq", **kwargs):
    from backend.storage.database import SessionLocal
    from backend.storage.models_extended import AuditSession, AuditResult, FAQRecord, PlatformFetchResult, SRSExtractionResult
    from datetime import datetime
    
    with SessionLocal() as db:
        session = db.query(AuditSession).get(session_id)
        if not session:
            return {"status": "FAILED", "error": "Session not found"}
        
        session.status = "RUNNING"
        session.progress_percent = 50
        db.commit()
        
        try:
            # Get fresh normalized data dynamically
            from backend.api.confirmation_routes import merge_normalized_data
            features = merge_normalized_data(db, session)
            variance_table = []
            developer_stats = {}
            total_planned = 0
            total_actual = 0
            total_variance = 0
            
            # Phase 1A: Aggregate Subtasks into Parents
            subtask_hours = {}
            subtasks_to_remove = set()
            for f in features:
                if f.get("rollup_parent_id"):
                    parent_id = f.get("rollup_parent_id")
                    subtask_hours[parent_id] = subtask_hours.get(parent_id, 0) + float(f.get("actual_hours") or 0)
                    subtasks_to_remove.add(f.get("issue_key"))
                    
            # Remove subtasks from active evaluation
            active_features = [f for f in features if f.get("issue_key") not in subtasks_to_remove]
            
            # Phase 1B: Aggregate by Requirement to prevent double counting
            requirement_map = {}
            
            for f in active_features:
                req_name = f.get("requirement") or "Unknown"
                planned = float(f.get("planned_hours") or 0)
                actual = float(f.get("actual_hours") or 0)
                
                issue_key = f.get("issue_key")
                rolled_up = subtask_hours.get(issue_key, 0)
                total_actual = actual + rolled_up
                
                dev = f.get("assigned_developer") or "Unassigned"
                module = f.get("module") or "General"
                status = f.get("status") or "unknown"
                
                # If the Jira ticket is Unmapped (Scope Drift), we treat each as a standalone Unknown requirement
                # rather than grouping all drift together
                if req_name == "Unknown":
                    req_name = f"Unknown (Drift: {issue_key})"
                    
                if req_name not in requirement_map:
                    requirement_map[req_name] = {
                        "planned_hours": planned, # Take planned hours ONLY ONCE per requirement
                        "actual_hours": 0,
                        "issues": [],
                        "module": module,
                        "devs": set(),
                        "status": status
                    }
                
                requirement_map[req_name]["actual_hours"] += total_actual
                if issue_key:
                    requirement_map[req_name]["issues"].append(str(issue_key))
                requirement_map[req_name]["devs"].add(dev)
                
                if dev not in developer_stats:
                    developer_stats[dev] = {"planned": 0, "actual": 0, "earned": 0, "modules": set()}
                
                developer_stats[dev]["actual"] += total_actual
                # We do not strictly add `planned` to dev stats here to avoid complex split-budget math, 
                # but we'll add the requirement's full planned budget to the primary developer
                developer_stats[dev]["modules"].add(module)
                
            # Distribute planned hours and earned value to developers
            srs_schedule_variance = 0.0
            ghost_hours = 0.0

            for req_name, data in requirement_map.items():
                is_unplanned = req_name.startswith("Unknown") or data["planned_hours"] == 0
                is_completed = data["status"].lower() in ["done", "resolved", "closed", "completed", "fixed"]
                
                if is_unplanned:
                    # Scenario F: Ghost Work credit (Earned = Actual)
                    earned_hours = data["actual_hours"]
                elif is_completed:
                    # Scenario B: Completed (Earned = Planned)
                    earned_hours = data["planned_hours"]
                else:
                    # Scenario A: In Progress (Earned = min(Actual, Planned))
                    earned_hours = min(data["actual_hours"], data["planned_hours"])

                if data["devs"]:
                    primary_dev = list(data["devs"])[0]
                    developer_stats[primary_dev]["planned"] += data["planned_hours"]
                    developer_stats[primary_dev]["earned"] += earned_hours
                
                total_planned += data["planned_hours"]
                total_actual += data["actual_hours"]
                variance = data["actual_hours"] - data["planned_hours"]
                total_variance += variance

                if is_unplanned:
                    ghost_hours += data["actual_hours"]
                else:
                    srs_schedule_variance += variance
                
                # Format Audit Explainability
                issues_str = ", ".join(data["issues"]) if data["issues"] else "No Jira Tickets"
                if is_unplanned and data["actual_hours"] > 0:
                    calculation_formula = f"{data['actual_hours']}h extra hours were logged due to task '{issues_str}', which was not in the planned SRS document."
                else:
                    calculation_formula = f"{data['actual_hours']}h (Actual) - {data['planned_hours']}h (Planned) = {variance}h (Variance)"
                evidence_str = f"Source: Jira ({issues_str}) | Formula: {calculation_formula}"
                
                variance_table.append({
                    "module": data["module"],
                    "requirement": req_name,
                    "planned_hours": data["planned_hours"],
                    "actual_hours": data["actual_hours"],
                    "variance": variance,
                    "status": data["status"],
                    "developer": ", ".join(data["devs"]) if data["devs"] else "Unassigned",
                    "severity": "high" if variance > 10 else "medium" if variance > 0 else "low",
                    "evidence": evidence_str,
                    "is_informational": False
                })
                
                
            developer_table = []
            for dev, stats in developer_stats.items():
                dev_var = stats["actual"] - stats["planned"]
                eff = (stats["earned"] / stats["actual"] * 100) if stats["actual"] > 0 else 0
                developer_table.append({
                    "developer": dev,
                    "assigned_modules": list(stats["modules"]),
                    "planned_hours": stats["planned"],
                    "actual_hours": stats["actual"],
                    "variance": dev_var,
                    "efficiency": round(eff, 2)
                })
                
            # A. Semantic Confidence
            valid_confs = [float(f.get("confidence_score", 1.0)) for f in features]
            semantic_confidence = int((sum(valid_confs) / len(valid_confs)) * 100) if valid_confs else 100
            
            # B. Predictive Risks & Risk Count
            predictive_risks = []
            for f in features:
                req = f.get("requirement") or "Unknown"
                dev = f.get("assigned_developer") or "Unassigned"
                status = str(f.get("status", "")).lower()
                planned = float(f.get("planned_hours") or 0)
                actual = float(f.get("actual_hours") or 0)
                conf = float(f.get("confidence_score", 1.0))
            
                if dev == "Unassigned" or not dev:
                    predictive_risks.append({"type": "Ownership Risk", "severity": "HIGH", "message": f"{req} is unassigned."})
                if status == "blocked":
                    predictive_risks.append({"type": "Blocker Risk", "severity": "CRITICAL", "message": f"{req} is blocked."})
                if planned > 0 and actual == 0 and status not in ("to do", "todo", "open"):
                    predictive_risks.append({"type": "Execution Risk", "severity": "MEDIUM", "message": f"{req} missing actual effort."})
                if conf < 0.75:
                    predictive_risks.append({"type": "Alignment Risk", "severity": "MEDIUM", "message": f"Low semantic match confidence for {req}."})
                if actual > 0 and planned == 0:
                    predictive_risks.append({"type": "Scope Risk", "severity": "MEDIUM", "message": f"Scope drift detected on {req}."})
            
            for v in variance_table:
                if v["variance"] > 8 or (v["planned_hours"] > 0 and v["variance"] > (v["planned_hours"] * 0.2)):
                    predictive_risks.append({"type": "Schedule Risk", "severity": "HIGH", "message": f"Large variance on {v['requirement']}."})
            
            # C. Health Score
            blocked_features = sum(1 for f in features if str(f.get("status", "")).lower() == "blocked")
            base_score = 100.0
            base_score -= len(predictive_risks) * 2.0
            base_score -= blocked_features * 5.0
            if total_planned > 0 and total_variance > 0:
                base_score -= min(20.0, (total_variance / total_planned) * 100.0)
            elif total_variance > 0:
                base_score -= min(20.0, total_variance)
            if semantic_confidence < 90:
                base_score -= (90 - semantic_confidence)
            health_score = max(0, min(100, int(base_score)))
            
            # D. Predicted Delay
            remaining_effort = sum(
                max(0, float(f.get("planned_hours") or 0) - float(f.get("actual_hours") or 0))
                for f in features 
                if str(f.get("status", "")).lower() not in ("done", "completed", "resolved", "closed")
            )
            profile = session.calendar_profile
            working_days_count = len(profile.working_days) if profile and profile.working_days else 5
            hours_per_day = profile.hours_per_day if profile and profile.hours_per_day else 8
            
            # Calculate true team size by taking the max of unique planned devs vs unique actual devs
            platform_res = db.query(PlatformFetchResult).filter(PlatformFetchResult.id == session.platform_fetch_result_id).first()
            raw_jira_features = platform_res.actual_data_json if platform_res else []
            jira_devs = set([f.get("assigned_developer") for f in raw_jira_features if f.get("assigned_developer") and f.get("assigned_developer") != "Unassigned"])
            
            srs_res = db.query(SRSExtractionResult).filter(SRSExtractionResult.id == session.srs_result_id).first()
            raw_srs_features = srs_res.extracted_json.get("features", []) if (srs_res and srs_res.extracted_json) else []
            srs_devs = set([f.get("assigned_developer") for f in raw_srs_features if f.get("assigned_developer") and f.get("assigned_developer") != "Unassigned"])
            
            developer_count = max(1, len(jira_devs), len(srs_devs))
            weekly_capacity = working_days_count * hours_per_day * developer_count
            predicted_delay = round(remaining_effort / weekly_capacity, 1) if weekly_capacity > 0 else 0.0
            
            # E. Executive Summary Narrative
            org_profile = platform_res.organization_profile_json if platform_res else {}
            project_key = org_profile.get("repo_name") or org_profile.get("project_key") or f"{session.platform_type.capitalize()} Project"
            
            # F. Root Cause Analysis
            root_cause_table = []
            if len(predictive_risks) > 0:
                root_cause_table.append({"evidence": f"Identified {len(predictive_risks)} predictive risks across execution, scope, and ownership.", "count": len(predictive_risks)})
            unassigned_count = sum(1 for f in features if not f.get("assigned_developer"))
            if unassigned_count > 0:
                root_cause_table.append({"evidence": f"Resource gap: {unassigned_count} features lack developer assignment.", "count": unassigned_count})
            if total_variance > 0:
                delayed_features = sum(1 for v in variance_table if v["variance"] > 0)
                root_cause_table.append({"evidence": f"Schedule slip of {total_variance}h originating from {delayed_features} requirements.", "count": delayed_features})
            if not root_cause_table:
                root_cause_table.append({"evidence": "No systemic root causes identified. Project is performing nominally.", "count": 0})
            
            # --- Dynamic FAQ Generation ---
            from backend.analysis.semantic_delay_analyzer import DelayAnalysisResult, DelayEvidence, DelayCategory
            from backend.analysis.faq_generator import FAQGenerator
            
            evidence_list = []
            primary_causes = []
            
            if unassigned_count > 0:
                evidence_list.append(DelayEvidence(
                    category=DelayCategory.UNASSIGNED_FEATURES,
                    severity=0.9,
                    description=f"{unassigned_count} features are unassigned.",
                    metadata={"unassigned_count": unassigned_count, "percentage": (unassigned_count / max(1, len(features))) * 100}
                ))
                primary_causes.append(DelayCategory.UNASSIGNED_FEATURES.value)
                
            if blocked_features > 0:
                blocked_items = [f.get("requirement") or "Unknown" for f in features if str(f.get("status", "")).lower() == "blocked"]
                evidence_list.append(DelayEvidence(
                    category=DelayCategory.BLOCKED_FEATURES,
                    severity=0.95,
                    description=f"{blocked_features} features are blocked.",
                    affected_features=blocked_items,
                    metadata={"blocked_count": blocked_features}
                ))
                primary_causes.append(DelayCategory.BLOCKED_FEATURES.value)
                
            missing_time = sum(1 for f in features if float(f.get("actual_hours") or 0) == 0)
            if missing_time > 0:
                evidence_list.append(DelayEvidence(
                    category=DelayCategory.MISSING_TIME_DATA,
                    severity=0.7,
                    description=f"{missing_time} features missing actual hours.",
                    metadata={"feature_count": missing_time, "percentage": (missing_time / max(1, len(features))) * 100}
                ))
                primary_causes.append(DelayCategory.MISSING_TIME_DATA.value)
                
            for dev, stats in developer_stats.items():
                if dev and dev != "Unassigned":
                    assigned_count = sum(1 for f in features if f.get("assigned_developer") == dev)
                    if assigned_count > 5:
                        evidence_list.append(DelayEvidence(
                            category=DelayCategory.CONTRIBUTOR_OVERLOAD,
                            severity=0.8,
                            description=f"{dev} is overloaded.",
                            metadata={"contributor": dev, "feature_count": assigned_count}
                        ))
                        primary_causes.append(DelayCategory.CONTRIBUTOR_OVERLOAD.value)
            
            completed_features = sum(1 for f in features if str(f.get("status", "")).lower() in ("done", "completed", "resolved", "closed"))
            in_progress_features = sum(1 for f in features if str(f.get("status", "")).lower() in ("in progress", "in_progress"))
            todo_features = sum(1 for f in features if str(f.get("status", "")).lower() in ("to do", "todo", "open"))
            
            analysis_result = DelayAnalysisResult(
                project_key=project_key,
                platform="jira",
                analysis_timestamp=datetime.utcnow(),
                total_features=len(features),
                completed_features=completed_features,
                in_progress_features=in_progress_features,
                blocked_features=blocked_features,
                unassigned_features=unassigned_count,
                evidence=evidence_list,
                severity_score=1.0 - (health_score / 100.0),
                primary_causes=primary_causes
            )
            
            faq_gen = FAQGenerator(analysis_result)
            dynamic_faqs = faq_gen.generate()
            
            faqs_json = [
                {
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category,
                    "relevance_score": int(faq.relevance_score * 100)
                } for faq in dynamic_faqs
            ]
            
            variance_json = {
                "variance_table": variance_table,
                "developer_table": developer_table,
                "root_cause_table": root_cause_table,
                "health_score": health_score,
                "schedule_variance": total_variance,
                "srs_schedule_variance": round(srs_schedule_variance, 1),
                "ghost_hours": round(ghost_hours, 1),
                "remaining_effort": remaining_effort,
                "requirement_drift": sum(1 for f in features if float(f.get("actual_hours") or 0) > 0 and float(f.get("planned_hours") or 0) == 0),
                "unassigned_features": unassigned_count,
                "semantic_confidence": semantic_confidence,
                "predictive_risks": predictive_risks,
                "risk_count": len(predictive_risks),
                "predicted_delay": predicted_delay,
                "project_key": project_key,
                "analysis_timestamp": str(datetime.utcnow()),
                "total_features": len(features),
                "completed_features": completed_features,
                "in_progress_features": in_progress_features,
                "todo_features": todo_features,
                "blocked_features": blocked_features,
                "faqs": faqs_json
            }
            
            audit_result = AuditResult(
                audit_session_id=session_id,
                
                variance_json=variance_json
            )
            db.add(audit_result)
            
            for faq in variance_json["faqs"]:
                db.add(FAQRecord(
                    audit_session_id=session_id,
                    question=faq["question"],
                    answer=faq["answer"],
                    category=faq["category"],
                    relevance_score=faq["relevance_score"]
                ))
                
            session.status = "COMPLETED"
            session.progress_percent = 100
            db.commit()
            
            return {"status": "COMPLETED", "session_id": session_id}
            
        except Exception as e:
            session.status = "FAILED"
            db.commit()
            return {"status": "FAILED", "error": str(e)}

