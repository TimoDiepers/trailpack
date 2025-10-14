from dataclasses import dataclass
from typing import Optional
import os

try:
    import streamlit as st
except ImportError:  # Streamlit not available outside the app
    st = None


@dataclass
class PystConfig:
    """Centralized PyST configuration"""
    host: str
    auth_token: Optional[str] = None
    timeout: int = 30

    @classmethod
    def from_env(cls):
        """Load configuration from Streamlit secrets with env fallback"""
        secret_host: Optional[str] = None
        secret_auth_token: Optional[str] = None

        if st is not None:
            try:
                secrets = st.secrets
            except Exception:
                secrets = None

            if secrets is not None:
                try:
                    secret_host = secrets["PYST_HOST"]
                except Exception:
                    secret_host = None

                try:
                    secret_auth_token = secrets["PYST_AUTH_TOKEN"]
                except Exception:
                    secret_auth_token = None

        return cls(
            host=secret_host or os.getenv("PYST_HOST", "http://localhost:8000"),
            auth_token=secret_auth_token or os.getenv("PYST_AUTH_TOKEN"),
            timeout=int(os.getenv("PYST_TIMEOUT", "30"))
        )


# Global config instance - use lazy loading to ensure secrets are available
_config: Optional[PystConfig] = None


def get_config() -> PystConfig:
    """Get or create the global config instance.
    
    Uses lazy loading to ensure Streamlit secrets are available when accessed.
    """
    global _config
    if _config is None:
        _config = PystConfig.from_env()
    return _config


# Backwards compatibility - config property that loads lazily
class _ConfigProxy:
    """Proxy object that loads config on first access."""
    
    def __getattr__(self, name):
        return getattr(get_config(), name)


config = _ConfigProxy()
