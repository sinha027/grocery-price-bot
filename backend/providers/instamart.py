from typing import Optional

from .base import BaseProvider, ProductResult


class InstamartProvider(BaseProvider):
    """
    Swiggy Instamart provider.

    This provider is intentionally NOT pretending to have live access yet.

    Live Instamart access requires the official Swiggy MCP/OAuth flow
    and production access from Swiggy.
    """

    platform_name = "Instamart"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    def search(
        self,
        search: str,
        location: str,
    ) -> ProductResult:

        # We do not have authorized live credentials yet.
        if not self.access_token:
            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=self.now_utc(),
                status="NOT_CONFIGURED",
                message=(
                    "Instamart live access is not configured yet."
                ),
            )

        # Live MCP integration will be implemented here
        # after authorized production access is available.
        return ProductResult(
            platform=self.platform_name,
            product_name=search,
            price=None,
            available=False,
            location=location,
            checked_at=self.now_utc(),
            status="NOT_IMPLEMENTED",
            message=(
                "Instamart live provider is awaiting "
                "official MCP integration."
            ),
        )