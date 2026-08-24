import re
from typing import Optional

from playwright.sync_api import sync_playwright

from .base import BaseProvider, ProductResult


class BigBasketProvider(BaseProvider):
    platform_name = "BigBasket"

    SEARCH_URL = "https://www.bigbasket.com/ps/"

    def __init__(self):
        pass

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        match = re.search(
            r"₹\s*([0-9]+(?:\.[0-9]+)?)",
            text,
        )

        if not match:
            return None

        try:
            return float(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _is_available(text: str) -> bool:
        lower = text.lower()

        if "currently unavailable" in lower:
            return False

        if "notify me" in lower:
            return False

        return bool(
            re.search(
                r"\badd\b",
                lower,
            )
        )

    @staticmethod
    def _is_requested_product(
        text: str,
        search: str,
    ) -> bool:

        text_lower = text.lower()
        search_lower = search.lower()

        if "amul" not in text_lower:
            return False

        if "taaza" not in text_lower:
            return False

        wants_1l = bool(
            re.search(
                r"\b1\s*l\b|\b1l\b|\b1000\s*ml\b",
                search_lower,
            )
        )

        if wants_1l:
            if not re.search(
                r"\b1\s*l\b",
                text_lower,
            ):
                return False

        if "taaza milk" in search_lower:
            if "taaza milk" not in text_lower:
                return False

        return True

    @staticmethod
    def _card_text(link) -> str:
        """
        Find the smallest useful parent containing:
        product name + size + price + Add.
        """

        current = link

        best_text = ""

        for _ in range(8):

            current = current.locator("..")

            try:
                text = current.inner_text().strip()
            except Exception:
                continue

            if not text:
                continue

            has_price = "₹" in text

            has_add = bool(
                re.search(
                    r"\bAdd\b",
                    text,
                    re.IGNORECASE,
                )
            )

            if has_price and has_add:

                if not best_text:
                    best_text = text

                elif len(text) < len(best_text):
                    best_text = text

        return best_text

    def _search_browser(
        self,
        search: str,
        location: str,
    ) -> Optional[dict]:

        search_url = (
            self.SEARCH_URL
            + "?q="
            + search.replace(" ", "+")
        )

        with sync_playwright() as p:

            # IMPORTANT:
            # Render runs on a headless Linux server
            # without a graphical X server.
            #
            # Therefore this MUST be headless=True.
            browser = p.chromium.launch(
                headless=True
            )

            page = browser.new_page(
                viewport={
                    "width": 1366,
                    "height": 900,
                }
            )

            try:
                page.goto(
                    search_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(8000)

                links = page.locator(
                    'a[href*="/pd/"]'
                )

                candidates = []

                for i in range(links.count()):

                    try:
                        link = links.nth(i)

                        href = link.get_attribute(
                            "href"
                        )

                        if not href:
                            continue

                        product_match = re.search(
                            r"/pd/(\d+)/",
                            href,
                        )

                        if not product_match:
                            continue

                        product_id = product_match.group(1)

                        if any(
                            item["product_id"]
                            == product_id
                            for item in candidates
                        ):
                            continue

                        text = self._card_text(link)

                        if not text:
                            continue

                        if not self._is_available(
                            text
                        ):
                            continue

                        if not self._is_requested_product(
                            text,
                            search,
                        ):
                            continue

                        price = self._extract_price(
                            text
                        )

                        if price is None:
                            continue

                        candidates.append(
                            {
                                "product_id": product_id,
                                "href": href,
                                "text": text,
                                "price": price,
                            }
                        )

                    except Exception:
                        continue

                if not candidates:
                    return None

                # Prefer the exact Taaza Milk pouch
                # when available.
                candidates.sort(
                    key=lambda item: (
                        "taaza milk"
                        not in item["text"].lower(),
                        "pouch"
                        not in item["text"].lower(),
                    )
                )

                return candidates[0]

            finally:
                browser.close()

    def search(
        self,
        search: str,
        location: str,
    ) -> ProductResult:

        checked_at = self.now_utc()

        try:
            result = self._search_browser(
                search,
                location,
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
                product_url=None,
                message=(
                    "BigBasket browser search failed: "
                    + str(exc)
                ),
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
                product_url=None,
                message=(
                    "No available BigBasket product "
                    "matched the requested search."
                ),
            )

        href = result["href"]

        if href.startswith("http"):
            product_url = href
        else:
            product_url = (
                "https://www.bigbasket.com"
                + href
            )

        return ProductResult(
            platform=self.platform_name,
            product_name=search,
            price=result["price"],
            available=True,
            location=location,
            checked_at=checked_at,
            status="LIVE",
            product_url=product_url,
            message=(
                "Live BigBasket price from "
                "browser search page."
            ),
        )