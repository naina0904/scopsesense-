import structlog
import logging
import re
import os

def mask_secrets(logger, log_method, event_dict):
    """Processor to mask secrets like PATs, tokens, and passwords in logs."""
    secrets_patterns = [
        re.compile(r"ghp_[a-zA-Z0-9]+"),  # GitHub PAT
        re.compile(r"Bearer\s+[a-zA-Z0-9\-\._~+/]+"), # Bearer tokens
        re.compile(r"api_key=['\"]?[a-zA-Z0-9]+['\"]?"), # API keys
    ]
    
    # Iterate through event dict and mask
    for key, value in event_dict.items():
        if isinstance(value, str):
            for pattern in secrets_patterns:
                value = pattern.sub("********", value)
            event_dict[key] = value
            
        # specifically mask keys named 'token', 'password', 'secret', 'key'
        if any(secret_term in key.lower() for secret_term in ["token", "password", "secret", "key", "authorization"]):
            event_dict[key] = "********"
            
    return event_dict

def configure_structlog():
    if structlog.is_configured():
        return
        
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            mask_secrets,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
def get_logger(name):
    configure_structlog()
    return structlog.get_logger(name)
