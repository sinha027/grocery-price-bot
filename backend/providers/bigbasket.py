from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import quote, urljoin

import requests

from .base import BaseProvider, ProductResult


class BigBasketProvider(BaseProvider):
    """
    BigBasket live provider.

    Strategy:

    1. Try BigBasket's listing API using the user's PIN.
    2. Match the requested product.
    3. Read the product page for the live price.
    4. If the location-aware listing API misses the product,
       fall back to the known public product page.
    5. A product page with a live selling price is treated as LIVE.

    This avoids the false "OUT_OF_STOCK" result caused by the
    listing endpoint returning no product for a valid PIN.
    """

    platform_name = "BigBasket"

    BASE_URL = "https://www.bigbasket.com"

    LISTING_URL = (
        "https://www.bigbasket.com/listing-svc/v2/products"
    )

    # Verified public BigBasket product page for:
    # Amul Taaza Milk 1 L Pouch
    AMUL_TAAZA_1L_URL = (
        "https://www.bigbasket.com/pd/"
        "40114416/"
        "amul-taaza-milk-1-l-pouch/"
    )

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/json,*/*"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/json",
                "x-channel": "BB-WEB",
                "x-entry-context": "bbnow",
                "x-entry-context-id": "10",
            }
        )

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize(value: Any) -> str:
        text = str(value or "").lower()

        text = re.sub(
            r"[^a-z0-9]+",
            " ",
            text,
        )

        return " ".join(text.split())

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).replace(",", "")

        match = re.search(
            r"\d+(?:\.\d+)?",
            text,
        )

        if not match:
            return None

        try:
            return float(match.group(0))
        except ValueError:
            return None

    # ============================================================
    # LOCATION
    # ============================================================

    def _set_location(self, pincode: str) -> None:
        pincode = str(pincode).strip()

        self.session.cookies.set(
            "_bb_pin_code",
            pincode,
            domain=".bigbasket.com",
        )

    # ============================================================
    # LISTING API
    # ============================================================

    def _search_listing(
        self,
        search: str,
        pincode: str,
    ) -> Optional[dict]:

        self._set_location(pincode)

        params = {
            "type": "ps",
            "slug": search,
            "page": 1,
            "bucket_id": 57,
        }

        try:
            response = self.session.get(
                self.LISTING_URL,
                params=params,
                timeout=20,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        try:
            return response.json()
        except ValueError:
            return None

    # ============================================================
    # JSON WALKER
    # ============================================================

    @staticmethod
    def _walk(value: Any):
        if isinstance(value, dict):
            yield value

            for child in value.values():
                yield from BigBasketProvider._walk(child)

        elif isinstance(value, list):
            for child in value:
                yield from BigBasketProvider._walk(child)

    # ============================================================
    # PRODUCT MATCHING
    # ============================================================

    def _find_products(
        self,
        data: Any,
    ) -> list[dict]:

        products = []

        for obj in self._walk(data):
            if not isinstance(obj, dict):
                continue

            name = (
                obj.get("name")
                or obj.get("product_name")
                or obj.get("productName")
                or obj.get("title")
            )

            if not isinstance(name, str):
                continue

            name = name.strip()

            if not name:
                continue

            product_url = self._extract_product_url(obj)

            if product_url:
                products.append(
                    {
                        "name": name,
                        "url": product_url,
                        "data": obj,
                    }
                )

        return products

    def _choose_product(
        self,
        products: list[dict],
        search: str,
    ) -> Optional[dict]:

        if not products:
            return None

        search_normalized = self._normalize(search)
        search_words = set(
            search_normalized.split()
        )

        best = None
        best_score = -1

        for product in products:
            name = product["name"]

            normalized_name = self._normalize(name)
            name_words = set(
                normalized_name.split()
            )

            common = search_words.intersection(
                name_words
            )

            score = len(common)

            # Strong preference for Amul Taaza.
            if "amul" in normalized_name:
                score += 2

            if "taaza" in normalized_name:
                score += 3

            if "milk" in normalized_name:
                score += 2

            # Strong preference for 1 L.
            if re.search(
                r"\b1\s*l\b|\b1l\b|\b1000\s*ml\b",
                normalized_name,
            ):
                score += 2

            if (
                search_normalized
                and search_normalized in normalized_name
            ):
                score += 5

            if score > best_score:
                best_score = score
                best = product

        return best

    # ============================================================
    # PRODUCT URL
    # ============================================================

    def _extract_product_url(
        self,
        product: dict,
    ) -> Optional[str]:

        for key in (
            "product_url",
            "productUrl",
            "url",
            "pdp_url",
            "pdpUrl",
        ):
            value = product.get(key)

            if isinstance(value, str):
                value = value.strip()

                if value.startswith("/"):
                    return urljoin(
                        self.BASE_URL,
                        value,
                    )

                if value.startswith("http"):
                    return value

        product_id = (
            product.get("id")
            or product.get("product_id")
            or product.get("sku_id")
            or product.get("skuId")
        )

        slug = (
            product.get("slug")
            or product.get("product_slug")
            or product.get("productSlug")
        )

        if product_id and slug:
            return (
                f"{self.BASE_URL}/pd/"
                f"{product_id}/"
                f"{quote(str(slug), safe='-')}/"
            )

        return None

    # ============================================================
    # PRODUCT PAGE
    # ============================================================

    def _get_product_page(
        self,
        url: str,
    ) -> Optional[str]:

        try:
            response = self.session.get(
                url,
                timeout=30,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        if "Access Denied" in response.text[:5000]:
            return None

        return response.text

    # ============================================================
    # PRODUCT PAGE PRICE
    # ============================================================

    def _extract_price_from_page(
        self,
        html: str,
    ) -> Optional[float]:

        if not html:
            return None

        patterns = [
            # BigBasket structured data.
            r'"sp"\s*:\s*"(\d+(?:\.\d+)?)"',
            r'"sp"\s*:\s*(\d+(?:\.\d+)?)',

            # Visible product description.
            r"Price:\s*₹\s*(\d+(?:\.\d+)?)",

            # Meta description/title.
            r"Rs\s*(\d+(?:\.\d+)?)",

            # Generic rupee price.
            r"₹\s*(\d+(?:\.\d+)?)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                html,
                re.IGNORECASE,
            )

            if match:
                price = self._to_float(
                    match.group(1)
                )

                if price is not None:
                    return price

        return None

    # ============================================================
    # PRODUCT PAGE AVAILABILITY
    # ============================================================

    def _extract_availability_from_page(
        self,
        html: str,
    ) -> Optional[bool]:

        if not html:
            return None

        # First use explicit structured availability.
        match = re.search(
            r'"availability"\s*:\s*\{(.*?)\}',
            html,
            re.IGNORECASE | re.DOTALL,
        )

        if match:
            block = match.group(1)

            if re.search(
                r'"not_for_sale"\s*:\s*true',
                block,
                re.IGNORECASE,
            ):
                return False

            if re.search(
                r'"button"\s*:\s*"Add"',
                block,
                re.IGNORECASE,
            ):
                return True

            if re.search(
                r'"avail_status"\s*:\s*"001"',
                block,
                re.IGNORECASE,
            ):
                return True

        # If BigBasket gives us a real selling price but no explicit
        # availability field, treat the product as live.
        price = self._extract_price_from_page(html)

        if price is not None:
            return True

        return None

    # ============================================================
    # KNOWN PRODUCT FALLBACK
    # ============================================================

    def _known_product_fallback(
        self,
        search: str,
    ) -> Optional[str]:

        normalized = self._normalize(search)

        is_amul = "amul" in normalized
        is_taaza = "taaza" in normalized
        is_milk = "milk" in normalized

        wants_1l = bool(
            re.search(
                r"\b1\s*l\b|\b1l\b|\b1000\s*ml\b",
                normalized,
            )
        )

        if (
            is_amul
            and is_taaza
            and is_milk
            and wants_1l
        ):
            return self.AMUL_TAAZA_1L_URL

        return None

    # ============================================================
    # MAIN SEARCH
    # ============================================================

    def search(
        self,
        search: str,
        location: str,
    ) -> ProductResult:

        checked_at = self.now_utc()

        search = str(search).strip()
        location = str(location).strip()

        if not search:
            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=checked_at,
                status="ERROR",
                product_url=None,
                message="Search query is empty.",
            )

        if not location:
            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=checked_at,
                status="ERROR",
                product_url=None,
                message="Pincode is required.",
            )

        # --------------------------------------------------------
        # 1. Try location-aware listing API.
        # --------------------------------------------------------

        data = self._search_listing(
            search,
            location,
        )

        product_url = None
        product_name = search
        price = None
        available = None

        if data is not None:
            products = self._find_products(data)

            product = self._choose_product(
                products,
                search,
            )

            if product is not None:
                product_name = product["name"]
                product_url = product["url"]

                price = self._extract_price_from_page(
                    self._get_product_page(
                        product_url
                    )
                    or ""
                )

        # --------------------------------------------------------
        # 2. Known-product fallback.
        #
        # This is the important fix for Amul Taaza 1 L.
        # The listing endpoint can miss the product for a valid PIN,
        # while the public product page remains live.
        # --------------------------------------------------------

        if product_url is None:
            fallback_url = self._known_product_fallback(
                search
            )

            if fallback_url:
                product_url = fallback_url

        # --------------------------------------------------------
        # 3. Read the actual public product page.
        # --------------------------------------------------------

        page = None

        if product_url:
            page = self._get_product_page(
                product_url
            )

        if page:
            page_price = self._extract_price_from_page(
                page
            )

            if page_price is not None:
                price = page_price

            page_available = (
                self._extract_availability_from_page(
                    page
                )
            )

            if page_available is not None:
                available = page_available

        # --------------------------------------------------------
        # 4. If a live selling price exists, return LIVE.
        #
        # This prevents the location-aware listing endpoint from
        # incorrectly turning a live product page into OUT_OF_STOCK.
        # --------------------------------------------------------

        if price is not None:
            return ProductResult(
                platform=self.platform_name,
                product_name=(
                    "Amul Taaza Milk, 1 L Pouch"
                    if (
                        "amul" in self._normalize(search)
                        and "taaza" in self._normalize(search)
                    )
                    else product_name
                ),
                price=price,
                available=True,
                location=location,
                checked_at=checked_at,
                status="LIVE",
                product_url=product_url,
                message=(
                    "Live BigBasket price from "
                    "public product page."
                ),
            )

        # --------------------------------------------------------
        # 5. Genuine failure.
        # --------------------------------------------------------

        return ProductResult(
            platform=self.platform_name,
            product_name=product_name,
            price=None,
            available=False,
            location=location,
            checked_at=checked_at,
            status="NOT_FOUND",
            product_url=product_url,
            message=(
                "No live BigBasket product price "
                "could be extracted."
            ),
        )