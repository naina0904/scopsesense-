import logging
from typing import List, Dict, Set
from dataclasses import dataclass, field

from backend.integrations.core.unified_schema import Feature, PlatformData, HierarchyNode

logger = logging.getLogger(__name__)

@dataclass
class HierarchyBuilder:
    """Service to construct a parent‑child hierarchy from a list of Features.

    It assigns ``parent_id``, ``root_id``, and ``hierarchy_level`` to each Feature
    and produces a collection of :class:`HierarchyNode` objects that are attached
    to the :class:`PlatformData` instance (see ``PlatformData.hierarchy_nodes``).
    """

    def build(self, platform_data: PlatformData) -> None:
        """Populate hierarchy information on *platform_data* in‑place.

        Steps:
        1. Index features by their ``id``.
        2. Resolve ``parent_id`` for each feature (already present for subtasks).
        3. Detect root nodes (features without a parent).
        4. Walk the tree to assign ``root_id`` and ``hierarchy_level``.
        5. Validate that there are no cycles.
        6. Store a list of :class:`HierarchyNode` in ``platform_data.hierarchy_nodes``.
        """
        # Index features for fast lookup
        feature_by_id: Dict[str, Feature] = {f.id: f for f in platform_data.features}
        logger.debug("Indexed %d features for hierarchy construction", len(feature_by_id))

        # Initialise hierarchy nodes
        nodes: Dict[str, HierarchyNode] = {}
        for fid, feature in feature_by_id.items():
            nodes[fid] = HierarchyNode(
                id=fid,
                external_id=fid,
                title=feature.name,
                node_type="FEATURE",
                parent_id=feature.parent_id,
                root_id=None,
                hierarchy_level=0,
                child_ids=[],
                platform=platform_data.platform.value if platform_data.platform else ""
            )

        # Helper to walk upwards and collect ancestry
        def resolve_ancestry(fid: str, visited: Set[str]) -> (str, int):
            """Return (root_id, level) for the feature ``fid``.

            ``visited`` tracks the recursion stack to detect cycles.
            """
            if fid in visited:
                raise ValueError(f"Cycle detected in hierarchy at feature {fid}")
            visited.add(fid)
            node = nodes[fid]
            if not node.parent_id:
                # Root node
                return fid, 0
            if node.parent_id not in nodes:
                # Missing parent – treat as root
                logger.warning("Parent %s of %s not found; treating as root", node.parent_id, fid)
                return fid, 0
            parent_root, parent_level = resolve_ancestry(node.parent_id, visited)
            return parent_root, parent_level + 1

        # Resolve ancestry for all nodes
        for fid in nodes:
            try:
                root_id, level = resolve_ancestry(fid, set())
                node = nodes[fid]
                node.root_id = root_id
                node.hierarchy_level = level
            except Exception as e:
                logger.error("Failed to resolve hierarchy for %s: %s", fid, e)

        # Populate children lists for convenience
        for node in nodes.values():
            if node.parent_id and node.parent_id in nodes:
                nodes[node.parent_id].child_ids.append(node.id)

        # Attach to PlatformData
        platform_data.hierarchy_nodes = list(nodes.values())
        logger.info("Hierarchy built with %d nodes", len(nodes))
