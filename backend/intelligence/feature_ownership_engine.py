import re
import os


class FeatureOwnershipEngine:

    # =================================================
    # ANALYZE OWNERSHIP
    # =================================================

    def analyze(
        self,
        features,
        activity,
        semantic_matches=None
    ):
        # Map feature names to their semantic matches from VectorStore if provided
        semantic_map = {}
        if semantic_matches:
            for match in semantic_matches:
                req = match.get("requirement")
                results = match.get("matches", {})
                if req and results:
                    semantic_map[req] = results

        ownership_results = []

        for feature in features:
            feature_name = feature.get("feature_name", "")
            feature_keywords = self._extract_keywords(feature_name)

            matched_files = set()
            contributors = set()
            evidence = []
            reasoning = []

            # 1. Use semantic code indexing if matches are available
            feature_matches = semantic_map.get(feature_name)
            if feature_matches and isinstance(feature_matches, dict):
                # Extract file paths from ChromaDB query results metadata
                docs_metas = feature_matches.get("metadatas", [[]])[0]
                feature_code_files = set()
                for meta in docs_metas:
                    if meta and "path" in meta:
                        feature_code_files.add(meta["path"].replace("\\", "/").lower())

                # Associate git activity with the semantically matched code files
                commit_count = 0
                for entry in activity:
                    author = entry.get("author", "")
                    files = entry.get("files", [])

                    for file_path in files:
                        normalized_git_file = file_path.replace("\\", "/").lower()
                        # Match if the git file path is a suffix of the indexed code chunk path
                        is_match = any(
                            normalized_git_file in idx_path or idx_path.endswith(normalized_git_file)
                            for idx_path in feature_code_files
                        )

                        if is_match:
                            matched_files.add(file_path)
                            if author:
                                contributors.add(author)
                            commit_count += 1
                            evidence.append({
                                "type": "semantic_code_indexing_match",
                                "file": file_path,
                                "author": author,
                                "message": entry.get("message", "")
                            })

                if commit_count > 0:
                    ownership_confidence = min(100, 40 + (commit_count * 10) + (len(contributors) * 5))
                    reasoning.append("Ownership inferred via semantic code search linked to Git commit history.")
                    reasoning.append(f"Mapped {len(matched_files)} implementation files to {len(contributors)} active developers.")
                    
                    ownership_results.append({
                        "feature": feature_name,
                        "matched_files": list(matched_files),
                        "contributors": list(contributors),
                        "ownership_confidence": ownership_confidence,
                        "contributing_factors": {
                            "file_path_matches": len(matched_files),
                            "semantic_message_matches": commit_count
                        },
                        "evidence": evidence,
                        "reasoning": reasoning
                    })
                    continue

            # 2. Fallback to keyword-based heuristics if no semantic matches or git associations were found
            match_score = 0
            semantic_score = 0

            for entry in activity:
                author = entry.get("author", "")
                files = entry.get("files", [])

                for file_path in files:
                    normalized = file_path.lower()
                    for keyword in feature_keywords:
                        if keyword in normalized:
                            matched_files.add(file_path)
                            if author:
                                contributors.add(author)
                            match_score += 1
                            evidence.append({
                                "type": "file_path_match",
                                "keyword": keyword,
                                "file": file_path,
                                "author": author
                            })

                message = entry.get("message", "").lower()
                for keyword in feature_keywords:
                    if keyword in message:
                        semantic_score += 1
                        if author:
                            contributors.add(author)
                        evidence.append({
                            "type": "commit_message_match",
                            "keyword": keyword,
                            "message": entry.get("message", ""),
                            "author": author
                        })

            ownership_confidence = min(
                100,
                (match_score * 25) + (semantic_score * 10)
            )
            reasoning.append("Ownership confidence starts with file-path keyword matches.")
            reasoning.append("Commit-message keyword matches add semantic support without replacing file evidence.")

            ownership_results.append({
                "feature": feature_name,
                "matched_files": list(matched_files),
                "contributors": list(contributors),
                "ownership_confidence": ownership_confidence,
                "contributing_factors": {
                    "file_path_matches": match_score,
                    "semantic_message_matches": semantic_score
                },
                "evidence": evidence,
                "reasoning": reasoning
            })

        return ownership_results

    # =================================================
    # KEYWORD EXTRACTION
    # =================================================

    def _extract_keywords(self, text):
        cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", text.lower())
        words = cleaned.split()

        ignored = {"system", "engine", "dashboard", "service"}
        keywords = [
            word
            for word in words
            if len(word) >= 4 and word not in ignored
        ]

        return keywords
