from datetime import datetime
from typing import Optional

from backend.providers import PROVIDERS


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for basic product matching.
    """

    if not text:
        return ""

    return " ".join(
        text.lower()
        .strip()
        .split()
    )


# ============================================================
# PROVIDER SEARCH
# ============================================================

def get_provider_results(
    search: str,
    location: str,
) -> list:
    """
    Ask every configured provider for a result.

    Providers may return:

        LIVE
        OUT_OF_STOCK
        NOT_CONFIGURED
        ERROR
        NOT_IMPLEMENTED

    Only LIVE results with a valid price can win
    the comparison.
    """

    results = []

    for provider in PROVIDERS:

        try:

            result = provider.search(
                search,
                location,
            )

            results.append({
                "platform": result.platform,

                "product_name": result.product_name,

                "price": result.price,

                "available": result.available,

                "status": result.status,

                "location": result.location,

                "checked_at": result.checked_at,

                "product_url": result.product_url,

                "message": result.message,

                "source": "PROVIDER",
            })

        except Exception as exc:

            results.append({
                "platform": provider.platform_name,

                "product_name": search,

                "price": None,

                "available": False,

                "status": "ERROR",

                "location": location,

                "checked_at": datetime.now().isoformat(),

                "product_url": None,

                "message": str(exc),

                "source": "PROVIDER",
            })

    return results


# ============================================================
# LIVE RESULTS ONLY
# ============================================================

def get_live_results(
    results: list,
) -> list:
    """
    Return only genuine LIVE results that contain a price.
    """

    return [
        item
        for item in results
        if (
            item.get("status") == "LIVE"
            and item.get("price") is not None
            and item.get("available") is True
        )
    ]


# ============================================================
# FIND CHEAPEST LIVE RESULT
# ============================================================

def find_cheapest_available(
    results: list,
) -> Optional[dict]:
    """
    Find the cheapest available LIVE product.
    """

    live_results = get_live_results(
        results
    )

    if not live_results:
        return None

    return min(
        live_results,
        key=lambda item: item["price"],
    )


# ============================================================
# FORMAT RESULTS
# ============================================================

def format_platform_results(
    results: list,
) -> list:
    """
    Format provider results for the frontend.
    """

    formatted = []

    for item in results:

        formatted.append({
            "platform": item.get(
                "platform"
            ),

            "price": item.get(
                "price"
            ),

            "available": item.get(
                "available",
                False,
            ),

            "status": item.get(
                "status"
            ),

            "location": item.get(
                "location"
            ),

            "checked_at": item.get(
                "checked_at"
            ),

            "source": item.get(
                "source"
            ),

            "product_url": item.get(
                "product_url"
            ),

            "message": item.get(
                "message"
            ),

            "product_name": item.get(
                "product_name"
            ),
        })

    return formatted


# ============================================================
# PRODUCT INFORMATION
# ============================================================

def build_product_info(
    search: str,
    results: list,
) -> Optional[dict]:
    """
    Build basic product information from the first
    provider result that has a product name.
    """

    for item in results:

        product_name = item.get(
            "product_name"
        )

        if product_name:

            return {
                "name": product_name,

                "brand": None,

                "quantity": None,

                "unit": None,
            }

    if search:

        return {
            "name": search,

            "brand": None,

            "quantity": None,

            "unit": None,
        }

    return None


# ============================================================
# MAIN LIVE COMPARISON
# ============================================================

def compare_product(
    search: str,
    location: str = "",
) -> dict:
    """
    Compare LIVE prices only.

    IMPORTANT:

    This function does NOT use demo prices.

    A platform can only win the comparison when:

        status == LIVE
        price is not None
        available == True

    If no provider has a genuine live price,
    the API clearly reports that live pricing
    is currently unavailable.
    """

    search = search.strip()

    location = location.strip()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not search:

        return {
            "success": False,

            "product_found": False,

            "available_anywhere": False,

            "search": search,

            "location": location,

            "message": (
                "Enter a product name."
            ),

            "prices": [],

            "providers": [],

            "cheapest": None,

            "maximum_saving": 0,
        }

    # --------------------------------------------------------
    # Get provider results
    # --------------------------------------------------------

    provider_results = get_provider_results(
        search,
        location,
    )

    # --------------------------------------------------------
    # Find LIVE results
    # --------------------------------------------------------

    live_results = get_live_results(
        provider_results
    )

    # --------------------------------------------------------
    # No provider results
    # --------------------------------------------------------

    if not provider_results:

        return {
            "success": False,

            "product_found": False,

            "available_anywhere": False,

            "search": search,

            "location": location,

            "message": (
                "No live price providers are configured."
            ),

            "prices": [],

            "providers": [],

            "cheapest": None,

            "maximum_saving": 0,

            "data_note": (
                "This comparison uses live provider "
                "data only. Demo prices are disabled."
            ),
        }

    # --------------------------------------------------------
    # No LIVE results
    # --------------------------------------------------------

    if not live_results:

        product = build_product_info(
            search,
            provider_results,
        )

        return {
            "success": True,

            "product_found": True,

            "available_anywhere": False,

            "search": search,

            "location": location,

            "product": product,

            "prices": format_platform_results(
                provider_results
            ),

            "providers": format_platform_results(
                provider_results
            ),

            "cheapest": None,

            "maximum_saving": 0,

            "data_note": (
                "No live price is currently available. "
                "Demo prices are disabled."
            ),
        }

    # --------------------------------------------------------
    # Find cheapest LIVE price
    # --------------------------------------------------------

    cheapest = find_cheapest_available(
        provider_results
    )

    if cheapest is None:

        return {
            "success": True,

            "product_found": True,

            "available_anywhere": False,

            "search": search,

            "location": location,

            "product": build_product_info(
                search,
                provider_results,
            ),

            "prices": format_platform_results(
                provider_results
            ),

            "providers": format_platform_results(
                provider_results
            ),

            "cheapest": None,

            "maximum_saving": 0,

            "data_note": (
                "No live price is currently available. "
                "Demo prices are disabled."
            ),
        }

    # --------------------------------------------------------
    # Calculate maximum saving
    # --------------------------------------------------------

    highest_price = max(
        item["price"]
        for item in live_results
    )

    maximum_saving = (
        highest_price
        - cheapest["price"]
    )

    # --------------------------------------------------------
    # Product information
    # --------------------------------------------------------

    product = build_product_info(
        search,
        provider_results,
    )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "success": True,

        "product_found": True,

        "available_anywhere": True,

        "search": search,

        "location": location,

        "product": product,

        "prices": format_platform_results(
            provider_results
        ),

        "providers": format_platform_results(
            provider_results
        ),

        "cheapest": {
            "platform": cheapest["platform"],

            "price": cheapest["price"],

            "available": True,

            "status": cheapest["status"],

            "location": cheapest["location"],

            "checked_at": cheapest["checked_at"],

            "source": "PROVIDER",

            "product_url": cheapest.get(
                "product_url"
            ),
        },

        "maximum_saving": maximum_saving,

        "data_note": (
            "LIVE provider data only. "
            "Demo prices are disabled."
        ),
    }