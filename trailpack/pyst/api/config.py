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


# Global config instance - loaded from environment variables
config = PystConfig.from_env()
