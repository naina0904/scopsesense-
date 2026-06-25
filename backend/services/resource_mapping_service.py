class ResourceMappingService:
    """Maps deterministic resource codes to developer levels."""
    
    MAPPING = {
        "s1": "Junior Developer",
        "a1": "Junior Developer",
        "s2": "Mid-Level Developer",
        "a2": "Mid-Level Developer",
        "s3": "Senior Developer",
        "a3": "Senior Developer",
    }
    
    @classmethod
    def map_resource(cls, resource_code: str) -> str:
        """
        Map a resource code to its developer level.
        Returns format: 'S2 (Mid-Level Developer)'
        """
        if not resource_code or str(resource_code).strip().lower() == "none":
            return "Unassigned"
            
        cleaned_code = str(resource_code).strip()
        level = cls.MAPPING.get(cleaned_code.lower())
        
        if level:
            return f"{cleaned_code.upper()} ({level})"
        
        # Fallback to the original code if no map matches
        return cleaned_code
