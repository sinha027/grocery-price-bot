from __future__ import annotations

import re
from typing import Any, Optional

import requests

from .base import BaseProvider, ProductResult


class JioMartProvider(BaseProvider):
    """
    Live JioMart provider.

    Uses the JioMart Vertex product-search API.
    """

    platform_name = "JioMart"

    API_URL = (
        "https://www.jiomart.com/"
        "ext/vertex/application/api/v1.0/products"
    )

    BASE_URL = "https://www.jiomart.com"

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "x-currency-code": "INR",
        })

    # ============================================================
    # HELPERS
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
    def _number(value: Any) -> Optional[float]:
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        match = re.search(
            r"\d+(?:\.\d+)?",
            str(value).replace(",", ""),
        )

        if not match:
            return None

        try:
            return float(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _walk(value: Any):
        """
        Recursively walk arbitrary JSON.
        """

        if isinstance(value, dict):
            yield value

            for child in value.values():
                yield from JioMartProvider._walk(child)

        elif isinstance(value, list):
            for child in value:
                yield from JioMartProvider._walk(child)

    # ============================================================
    # API
    # ============================================================

    def _get_products_api(
        self,
        search: str,
        pincode: str,
    ) -> Optional[dict]:

        params = {
            "f": (
                "journey:quickcommerce:::"
                "store_ids:3094||3164||3230||208650||259632"
                ":::searchType:global"
            ),
            "page_id": "*",
            "page_size": "50",
            "q": search,
        }

        location_detail = (
            '{"country":"INDIA",'
            '"country_iso_code":"IN",'
            '"city":"PUNE",'
            f'"pincode":"{pincode}",'
            '"state":"MAHARASHTRA"}'
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "application/json, text/plain, */*"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "x-currency-code": "INR",
            "x-location-detail": location_detail,
        }

        try:
            response = self.session.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=20,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None

        return data

    # ============================================================
    # FIND PRODUCT OBJECTS
    # ============================================================

    def _find_product_objects(
        self,
        data: dict,
    ) -> list[dict]:

        found = []

        for obj in self._walk(data):

            if not isinstance(obj, dict):
                continue

            name = obj.get("name")

            if not isinstance(name, str):
                continue

            if not name.strip():
                continue

            # JioMart product objects normally contain uid.
            uid = (
                obj.get("uid")
                or obj.get("id")
                or obj.get("item_id")
                or obj.get("itemId")
            )

            if uid is None:
                continue

            # Product responses generally contain pricing
            # information somewhere in the object.
            has_price = (
                "price" in obj
                or "selling_price" in obj
                or "sale_price" in obj
            )

            if not has_price:
                continue

            found.append(obj)

        return found

    # ============================================================
    # MATCH PRODUCT
    # ============================================================

    def _select_product(
        self,
        products: list[dict],
        search: str,
    ) -> Optional[dict]:

        if not products:
            return None

        wanted = self._normalize(search)

        wanted_words = set(
            wanted.split()
        )

        best = None
        best_score = -1

        for product in products:

            name = self._normalize(
                product.get("name")
            )

            if not name:
                continue

            name_words = set(
                name.split()
            )

            common_words = (
                wanted_words & name_words
            )

            score = len(common_words)

            # Strong exact/sub-string match.
            if wanted in name:
                score += 10

            # Product name inside query.
            if name in wanted:
                score += 5

            # Milk is particularly important for
            # the current grocery use case.
            if "milk" in wanted_words and "milk" in name_words:
                score += 2

            # Quantity matching.
            requested_quantity = re.search(
                r"(\d+(?:\.\d+)?)\s*(ml|l|g|kg)\b",
                wanted,
            )

            if requested_quantity:

                requested_value = (
                    requested_quantity.group(1)
                )

                requested_unit = (
                    requested_quantity.group(2)
                )

                product_text = self._normalize(
                    " ".join(
                        str(product.get(key, ""))
                        for key in (
                            "name",
                            "net_quantity",
                            "net-quantity-value",
                            "net-quantity-unit",
                            "quantity",
                            "weight",
                        )
                    )
                )

                if (
                    requested_value in product_text
                    and requested_unit in product_text
                ):
                    score += 4

            if score > best_score:
                best_score = score
                best = product

        return best

    # ============================================================
    # PRICE
    # ============================================================

    def _extract_price(
        self,
        product: dict,
    ) -> Optional[float]:

        price = product.get("price")

        if isinstance(price, dict):

            effective = price.get(
                "effective"
            )

            if isinstance(effective, dict):

                for key in (
                    "min",
                    "max",
                    "value",
                ):

                    value = self._number(
                        effective.get(key)
                    )

                    if value is not None:
                        return value

            for key in (
                "effective",
                "selling",
                "selling_price",
                "sale",
                "min",
                "max",
            ):

                value = self._number(
                    price.get(key)
                )

                if value is not None:
                    return value

        for key in (
            "selling_price",
            "sale_price",
            "sellingPrice",
            "offer_price",
            "offerPrice",
        ):

            value = self._number(
                product.get(key)
            )

            if value is not None:
                return value

        return None

    # ============================================================
    # AVAILABILITY
    # ============================================================

    def _extract_availability(
        self,
        product: dict,
    ) -> bool:

        sellable = product.get(
            "sellable"
        )

        if isinstance(sellable, bool):
            return sellable

        in_stock = product.get(
            "in_stock_variant"
        )

        if isinstance(in_stock, bool):
            return in_stock

        variants = product.get(
            "instock_variants"
        )

        if isinstance(variants, dict):

            sizes = variants.get(
                "sizes"
            )

            if isinstance(sizes, list):
                return bool(sizes)

        return False

    # ============================================================
    # PRODUCT URL
    # ============================================================

    def _extract_product_url(
        self,
        product: dict,
    ) -> Optional[str]:

        action = product.get(
            "action"
        )

        if isinstance(action, dict):

            page = action.get(
                "page"
            )

            if isinstance(page, dict):

                params = page.get(
                    "params"
                )

                if isinstance(params, dict):

                    slug = params.get(
                        "slug"
                    )

                    if isinstance(slug, list):
                        slug = (
                            slug[0]
                            if slug
                            else None
                        )

                    if isinstance(
                        slug,
                        str,
                    ) and slug:

                        return (
                            f"{self.BASE_URL}"
                            f"/product/{slug}"
                        )

        slug = product.get(
            "slug"
        )

        if isinstance(
            slug,
            str,
        ) and slug:

            return (
                f"{self.BASE_URL}"
                f"/product/{slug}"
            )

        uid = (
            product.get("uid")
            or product.get("id")
            or product.get("item_id")
            or product.get("itemId")
        )

        name = product.get(
            "name"
        )

        if uid is not None and name:

            slug = self._normalize(
                name
            ).replace(
                " ",
                "-",
            )

            return (
                f"{self.BASE_URL}"
                f"/product/{slug}-{uid}"
            )

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
                message="Pincode is required.",
            )

        data = self._get_products_api(
            search,
            location,
        )

        if data is None:

            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=checked_at,
                status="ERROR",
                message=(
                    "JioMart product API request "
                    "failed for this location."
                ),
            )

        products = self._find_product_objects(
            data
        )

        product = self._select_product(
            products,
            search,
        )

        if product is None:

            return ProductResult(
                platform=self.platform_name,
                product_name=search,
                price=None,
                available=False,
                location=location,
                checked_at=checked_at,
                status="NOT_FOUND",
                message=(
                    "JioMart API returned data, "
                    "but no matching product "
                    "was found."
                ),
            )

        product_name = (
            product.get("name")
            or search
        )

        price = self._extract_price(
            product
        )

        available = self._extract_availability(
            product
        )

        product_url = (
            self._extract_product_url(
                product
            )
        )

        if price is not None:

            return ProductResult(
                platform=self.platform_name,
                product_name=product_name,
                price=price,
                available=available,
                location=location,
                checked_at=checked_at,
                status="LIVE",
                product_url=product_url,
                message=(
                    "Live JioMart Vertex API price."
                ),
            )

        return ProductResult(
            platform=self.platform_name,
            product_name=product_name,
            price=None,
            available=available,
            location=location,
            checked_at=checked_at,
            status="ERROR",
            product_url=product_url,
            message=(
                "JioMart product was found, "
                "but no usable live price "
                "was returned."
            ),
        )