"""
Base adapter for platform integrations (GitHub, JIRA, etc).
All platform-specific adapters must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.integrations.core.unified_schema import PlatformData, PlatformType


class BaseAdapter(ABC):
    """
    Abstract base class for platform integrations.
    Each adapter normalizes platform-specific data to PlatformData schema.
    """
    
    def __init__(self, auth_credentials: Dict[str, str]):
        """
        Initialize adapter with authentication credentials.
        
        Args:
            auth_credentials: Platform-specific auth details
                For GitHub: {"pat": "token_value"}
                For JIRA: {"api_token": "token_value", "domain": "company.atlassian.net"}
        """
        self.auth_credentials = auth_credentials
        self.platform_type: PlatformType = None
        self.authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the platform.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def fetch_raw_data(self) -> Dict[str, Any]:
        """
        Fetch raw platform-specific data.
        
        Returns:
            Dict containing raw platform data
        """
        raise NotImplementedError
    
    @abstractmethod
    def normalize(self) -> PlatformData:
        """
        Convert raw platform data to unified PlatformData schema.
        
        Returns:
            PlatformData: Normalized, platform-agnostic representation
        """
        raise NotImplementedError
    
    def execute(self) -> Optional[PlatformData]:
        """
        Execute full integration: authenticate -> fetch -> normalize.
        
        Returns:
            PlatformData if successful, None if failed
        """
        if not self.authenticate():
            return None
        
        raw_data = self.fetch_raw_data()
        if not raw_data:
            return None
        
        return self.normalize()