"""TinyFish configuration scaffold.

The exact request/response contract must be checked against the team's
TinyFish account/API documentation before enabling live browser extraction.
"""
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class TinyFishConfig:
    api_key: str
    api_url: str

    @property
    def configured(self) -> bool:
        return bool(self.api_key.strip() and self.api_url.strip())

def load_config() -> TinyFishConfig:
    return TinyFishConfig(
        api_key=os.getenv("TINYFISH_API_KEY", ""),
        api_url=os.getenv("TINYFISH_API_URL", ""),
    )

def status() -> dict[str, object]:
    config = load_config()
    return {
        "configured": config.configured,
        "live_extraction_enabled": False,
        "message": (
            "Credentials detected, but live extraction is disabled until the "
            "TinyFish API contract is verified."
            if config.configured else
            "Set TINYFISH_API_KEY and TINYFISH_API_URL in your local environment."
        ),
    }
