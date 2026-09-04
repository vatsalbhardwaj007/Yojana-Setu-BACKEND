"""Configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMES_DIR = PROJECT_ROOT / "data" / "schemes"


@dataclass
class WhatsAppConfig:
    verify_token: str = ""
    access_token: str = ""
    phone_number_id: str = ""
    app_secret: str = ""
    graph_api_version: str = "v23.0"
    m2_backend_url: str = "http://localhost:8000"
    m2_api_key: str = ""
    m2_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "WhatsAppConfig":
        return cls(
            verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", ""),
            access_token=os.environ.get("WHATSAPP_ACCESS_TOKEN", ""),
            phone_number_id=os.environ.get("WHATSAPP_PHONE_NUMBER_ID", ""),
            app_secret=os.environ.get("WHATSAPP_APP_SECRET", ""),
            graph_api_version=os.environ.get("GRAPH_API_VERSION", "v23.0"),
            m2_backend_url=os.environ.get("M2_BACKEND_URL", "http://localhost:8000"),
            m2_api_key=os.environ.get("M2_API_KEY", ""),
            m2_timeout=float(os.environ.get("M2_TIMEOUT", "10")),
        )

    def is_whatsapp_configured(self) -> bool:
        return bool(self.verify_token and self.access_token and self.phone_number_id)
