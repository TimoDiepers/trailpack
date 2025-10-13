from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path

@dataclass
class PystConfig:
    """Centralized PyST configuration"""
    host: str
    auth_token: Optional[str] = None
    timeout: int = 30

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        # Try to load .env file if it exists
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).resolve().parents[3] / '.env'
            if env_path.exists():
                load_dotenv(env_path)
        except ImportError:
            pass  # dotenv not installed, use existing env vars

        return cls(
            host=os.getenv("PYST_HOST", "http://localhost:8000"),
            auth_token=os.getenv("PYST_AUTH_TOKEN"),
            timeout=int(os.getenv("PYST_TIMEOUT", "30"))
        )


# Global config instance - loaded from environment variables
config = PystConfig.from_env()