# backend/services/semantic_matcher.py
"""Semantic Matcher Service

Provides hierarchy‑aware semantic matching between SRS modules (represented by
`SRSNode`) and platform features (`Feature`). The matcher uses the existing
`VectorStore` and an embedding engine to perform a similarity search. For each
SRS node we query the vector store for the most similar code/document chunks
and return the matched features along with confidence scores.

The current implementation is a thin wrapper around the generic `VectorStore`
semantic search. Future enhancements (e.g., hierarchy expansion, confidence
thresholding, persistence) will build on this foundation.
"""

from typing import List, Dict, Any, Optional

# Local imports – these modules exist in the repository
from backend.models.srs_node import SRSNode
from backend.integrations.core.unified_schema import Feature
from backend.semantic.vector_store import VectorStore


class SemanticMatcher:
    """Match SRS modules to platform features using semantic similarity.

    Parameters
    ----------
    vector_store: VectorStore
        Instance of the vector store containing indexed code/document chunks.
    embedding_engine: Any
        Engine providing a `generate_embedding(text: str) -> List[float]` method.
    top_k: int, optional (default=5)
        Number of candidate matches to return per SRS node.
    namespace: str, optional
        Namespace within the vector store to limit the search (e.g., a project
        identifier). If ``None`` the default namespace of the store is used.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_engine: Any,
        top_k: int = 5,
        namespace: Optional[str] = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_engine = embedding_engine
        self.top_k = top_k
        self.namespace = namespace

    def match_modules(
        self,
        srs_nodes: List[SRSNode],
        features: List[Feature],
    ) -> List[Dict[str, Any]]:
        """Perform semantic matching for a list of SRS nodes.

        Returns a list of dictionaries, one per SRS node, containing the
        original node and a list of matched feature identifiers with confidence.
        """
        matches: List[Dict[str, Any]] = []
        for node in srs_nodes:
            query_text = f"{node.title}\n{node.description}".strip()
            if not query_text:
                # Skip empty nodes
                continue

            # Perform semantic search against the vector store
            results = self.vector_store.semantic_search(
                query=query_text,
                embedding_engine=self.embedding_engine,
                top_k=self.top_k,
                namespace=self.namespace,
            )

            # Extract IDs, confidences, and metadata (if present)
            doc_ids = results.get("ids", [[]])[0]
            confidences = results.get("confidence", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            # Map matched document IDs back to platform features if possible.
            # For now we perform a simple heuristic: if the metadata contains a
            # 'path' that includes a feature identifier, we use it; otherwise we
            # fall back to returning the raw IDs.
            matched_feature_ids: List[str] = []
            for meta in metadatas:
                feature_id = None
                if isinstance(meta, dict):
                    # Expected metadata shape from code indexing includes a
                    # 'path' key like ".../features/<feature_id>.py".
                    path = meta.get("path", "")
                    # Attempt to extract a UUID pattern (simple heuristic).
                    # Feature IDs in the system are typically alphanumeric.
                    parts = path.split('/')
                    if parts:
                        candidate = parts[-1].split('.')[0]
                        feature_id = candidate
                if feature_id:
                    matched_feature_ids.append(feature_id)
                else:
                    # Use the document ID as a fallback identifier.
                    matched_feature_ids.append(str(meta.get("id", "")))

            matches.append(
                {
                    "srs_node_id": node.id,
                    "title": node.title,
                    "matched_feature_ids": matched_feature_ids,
                    "confidence_scores": confidences,
                    "matched_documents": doc_ids,
                }
            )
        return matches

# End of file
