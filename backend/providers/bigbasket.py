import re
from typing import Optional

import requests

from .base import BaseProvider, ProductResult


class BigBasketProvider(BaseProvider):
    platform_name = "BigBasket"

    BASE_URL = "https://www.bigbasket.com"

    # Known BigBasket product pages can be used directly when
    # the requested product matches them.
    KNOWN_PRODUCTS = {
        "amul taaza milk 1l": {
            "url": (
                "https://www.bigbasket.com/"
                "pd/40114416/"
                "amul-taaza-milk-1-l-pouch/"
            ),
            "name": "Amul Taaza Milk, 1 L Pouch",
        }
    }

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,image/avif,"
                    "image/webp,*/*;q=0.8"
                ),
                "Accept-Language": (
                    "en-US,en;q=0.9"
                ),
            }
        )

    @staticmethod
    def _normalise(text: str) -> str:
        text = text.lower()

        text = text.replace("&nbsp;", " ")

        text = re.sub(
            r"[^a-z0-9]+",
            " ",
            text,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    @staticmethod
    def _extract_price(html: str) -> Optional[float]:

        patterns = [
            # Example:
            # Price: ₹59
            r"Price:\s*₹\s*([0-9]+(?:\.[0-9]+)?)",

            # Example:
            # ₹59
            r"₹\s*([0-9]+(?:\.[0-9]+)?)",

            # Example:
            # Rs 59
            r"\bRs\.?\s*([0-9]+(?:\.[0-9]+)?)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.IGNORECASE,
            )

            if match:

                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    @staticmethod
    def _extract_title(html: str) -> Optional[str]:

        # First try the HTML <title>.
        match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            re.IGNORECASE | re.DOTALL,
        )

        if match:

            title = re.sub(
                r"<[^>]+>",
                " ",
                match.group(1),
            )

            title = re.sub(
                r"\s+",
                " ",
                title,
            ).strip()

            if title:
                return title

        # Fallback: product title in common BigBasket metadata.
        patterns = [
            r'"name"\s*:\s*"([^"]+)"',
            r'"productName"\s*:\s*"([^"]+)"',
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return None

    @staticmethod
    def _is_available(html: str) -> bool:

        lower = html.lower()

        unavailable_phrases = [
            "currently unavailable",
            "notify me",
            "out of stock",
            "sold out",
        ]

        for phrase in unavailable_phrases:

            if phrase in lower:
                return False

        # BigBasket product pages commonly expose
        # an Add to basket / Add button when available.
        available_phrases = [
            "add to basket",
            "add to cart",
            ">add<",
            '"add"',
        ]

        for phrase in available_phrases:

            if phrase in lower:
                return True

        # If a valid price exists, consider the product
        # potentially available.
        return BigBasketProvider._extract_price(
            html
        ) is not None

    @staticmethod
    def _matches_product(
        html: str,
        search: str,
    ) -> bool:

        search_normalised = (
            BigBasketProvider._normalise(search)
        )

        html_normalised = (
            BigBasketProvider._normalise(html)
        )

        # Brand
        if "amul" in search_normalised:

            if "amul" not in html_normalised:
                return False

        # Product name
        if "taaza" in search_normalised:

            if "taaza" not in html_normalised:
                return False

        # Milk
        if "milk" in search_normalised:

            if "milk" not in html_normalised:
                return False

        # 1 L / 1L / 1000 ml
        wants_1l = bool(
            re.search(
                r"\b1\s*l\b|\b1l\b|\b1000\s*ml\b",
                search_normalised,
            )
        )

        if wants_1l:

            has_1l = bool(
                re.search(
                    r"\b1\s*l\b|\b1l\b|\b1000\s*ml\b",
                    html_normalised,
                )
            )

            if not has_1l:
                return False

        return True

    def _get_product_url(
        self,
        search: str,
    ) -> Optional[str]:

        search_normalised = (
            self._normalise(search)
        )

        # Exact known product mapping.
        if search_normalised in self.KNOWN_PRODUCTS:

            return self.KNOWN_PRODUCTS[
                search_normalised
            ]["url"]

        # Also support common variations such as:
        # "Amul Taaza Milk 1 L"
        # "Amul Taaza Milk 1L"
        if (
            "amul" in search_normalised
            and "taaza" in search_normalised
            and "milk" in search_normalised
            and (
                "1 l" in search_normalised
                or "1l" in search_normalised
            )
        ):

            return self.KNOWN_PRODUCTS[
                "amul taaza milk 1l"
            ]["url"]

        return None

    def _fetch_product(
        self,
        url: str,
    ) -> Optional[dict]:

        response = self.session.get(
            url,
            timeout=45,
            allow_redirects=True,
        )

        response.raise_for_status()

        html = response.text

        if not html:
            return None

        if "Access Denied" in html:
            raise RuntimeError(
                "BigBasket HTTP request was blocked."
            )

        price = self._extract_price(html)

        if price is None:
            return None

        title = self._extract_title(html)

        available = self._is_available(html)

        return {
            "price": price,
            "title": title,
            "available": available,
            "url": response.url,
        }

    def search(
        self,
        search: str,
        location: str,
    ) -> ProductResult:

        checked_at = self.now_utc()

        try:

            product_url = self._get_product_url(
                search
            )

            if not product_url:

                return ProductResult(
                    platform=self.platform_name,
                    product_name=search,
                    price=None,
                    available=False,
                    location=location,
                    checked_at=checked_at,
                    status="NOT_FOUND",
                    product_url=None,
                    message=(
                        "No BigBasket product mapping "
                        "matched the requested search."
                    ),
                )

            result = self._fetch_product(
                product_url
            )

            if result is None:

                return ProductResult(
                    platform=self.platform_name,
                    product_name=search,
                    price=None,
                    available=False,
                    location=location,
                    checked_at=checked_at,
                    status="NOT_FOUND",
                    product_url=product_url,
                    message=(
                        "BigBasket product page was "
                        "reachable but no valid price "
                        "was found."
                    ),
                )

            if not result["available"]:

                return ProductResult(
                    platform=self.platform_name,
                    product_name=(
                        result["title"]
                        or search
                    ),
                    price=None,
                    available=False,
                    location=location,
                    checked_at=checked_at,
                    status="NOT_FOUND",
                    product_url=result["url"],
                    message=(
                        "BigBasket product is currently "
                        "unavailable."
                    ),
                )

            return ProductResult(
                platform=self.platform_name,
                product_name=(
                    "Amul Taaza Milk, 1 L Pouch"
                    if (
                        "amul" in search.lower()
                        and "taaza" in search.lower()
                    )
                    else (
                        result["title"]
                        or search
                    )
                ),
                price=result["price"],
                available=True,
                location=location,
                checked_at=checked_at,
                status="LIVE",
                product_url=result["url"],
                message=(
                    "Live BigBasket price from "
                    "HTTP product page."
                ),
            )

        except requests.RequestException as exc:

            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=checked_at,
                status="ERROR",
                product_url=product_url
                if "product_url" in locals()
                else None,
                message=(
                    "BigBasket HTTP request failed: "
                    + str(exc)
                ),
            )

        except Exception as exc:

            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=checked_at,
                status="ERROR",
                product_url=product_url
                if "product_url" in locals()
                else None,
                message=(
                    "BigBasket provider failed: "
                    + str(exc)
                ),
            )