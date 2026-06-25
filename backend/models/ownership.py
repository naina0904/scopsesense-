"""Model for ownership history events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OwnershipEvent:
    """Represents a change of ownership for an SRS node.

    Attributes
    ----------
    owner: str
        Identifier of the person/team taking ownership (e.g., email or username).
    role: str
        Role at the time of ownership (e.g., 'developer', 'reviewer').
    timestamp: datetime
        When the ownership was recorded.
    notes: Optional[str]
        Free‑form notes about the hand‑off.
    """

    owner: str
    role: str
    timestamp: datetime
    notes: Optional[str] = None
