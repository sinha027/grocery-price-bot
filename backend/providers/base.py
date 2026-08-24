from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ProductResult:
    platform: str
    product_name: str
    price: Optional[float]
    available: bool
    location: str
    checked_at: str
    status: str
    product_url: Optional[str] = None
    message: Optional[str] = None


class BaseProvider:
    """
    Common interface for grocery platform providers.
    """

    platform_name = "Unknown"

    def search(
        self,
        search: str,
        location: str,
    ) -> ProductResult:
        raise NotImplementedError(
            "Provider must implement search()"
        )

    @staticmethod
    def now_utc() -> str:
        return datetime.now(timezone.utc).isoformat()