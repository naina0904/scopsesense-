from enum import Enum

class Role(str, Enum):
    """User roles used throughout the system.
    
    * ``ADMIN`` – Full access, can manage users and all settings.
    * ``MANAGER`` – Can confirm SRS, platform data, and calendar; can run analyses.
    * ``ANALYST`` – Read‑only access to analysis results and chat.
    """
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
