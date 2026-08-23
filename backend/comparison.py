from datetime import datetime


# ============================================================
# DEMO PRODUCT DATABASE
# ============================================================
#
# IMPORTANT:
# These are currently DEMO prices.
# Later we will replace these with legitimate live data sources.
#
# ============================================================

PRODUCTS = [

    {
        "name": "Amul Taaza Milk 1L",
        "brand": "Amul",
        "quantity": 1,
        "unit": "L",

        "prices": {
            "Blinkit": 68,
            "Zepto": 66,
            "Instamart": 69,
            "BigBasket": 67,
        },

        "availability": {
            "Blinkit": True,
            "Zepto": False,
            "Instamart": True,
            "BigBasket": True,
        },
    },


    {
        "name": "Amul Butter 500g",
        "brand": "Amul",
        "quantity": 500,
        "unit": "g",

        "prices": {
            "Blinkit": 245,
            "Zepto": 239,
            "Instamart": 242,
            "BigBasket": 241,
        },

        "availability": {
            "Blinkit": True,
            "Zepto": True,
            "Instamart": False,
            "BigBasket": True,
        },
    },


    {
        "name": "Tata Salt 1kg",
        "brand": "Tata",
        "quantity": 1,
        "unit": "kg",

        "prices": {
            "Blinkit": 28,
            "Zepto": 27,
            "Instamart": 29,
            "BigBasket": 28,
        },

        "availability": {
            "Blinkit": True,
            "Zepto": True,
            "Instamart": True,
            "BigBasket": False,
        },
    },

]


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    return (
        text
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace(",", " ")
        .strip()
    )


# ============================================================
# PRODUCT MATCHING
# ============================================================

def product_matches(search, product):

    search = normalize_text(search)

    product_name = normalize_text(
        product["name"]
    )

    brand = normalize_text(
        product["brand"]
    )

    # --------------------------------------------------------
    # Exact product-name match
    # --------------------------------------------------------

    if search == product_name:
        return True


    # --------------------------------------------------------
    # All search words must exist in the product
    # --------------------------------------------------------

    search_words = search.split()

    searchable_text = (
        product_name
        + " "
        + brand
    )

    for word in search_words:

        if word not in searchable_text:
            return False

    return True


# ============================================================
# SEARCH PRODUCTS
# ============================================================

def search_products(
    search: str,
    location: str = ""
):

    results = []

    for product in PRODUCTS:

        if not product_matches(
            search,
            product
        ):
            continue


        # ----------------------------------------------------
        # Create result for every platform
        # ----------------------------------------------------

        for platform, price in product["prices"].items():

            available = product[
                "availability"
            ].get(
                platform,
                False
            )


            checked_at = (
                datetime.now().isoformat()
            )


            results.append({

                "name": product["name"],

                "brand": product["brand"],

                "quantity": product["quantity"],

                "unit": product["unit"],

                "platform": platform,

                "price": price,

                "available": available,

                "location": location,

                "checked_at": checked_at,

            })


    return results


# ============================================================
# FIND CHEAPEST AVAILABLE PRODUCT
# ============================================================

def find_cheapest_available(
    results
):

    available_products = [

        item

        for item in results

        if item["available"] is True

    ]


    if not available_products:

        return None


    return min(
        available_products,
        key=lambda item: item["price"]
    )


# ============================================================
# GET AVAILABLE PRODUCTS
# ============================================================

def get_available_products(
    results
):

    return [

        item

        for item in results

        if item["available"] is True

    ]


# ============================================================
# MAIN COMPARISON FUNCTION
# ============================================================

def compare_product(
    search: str,
    location: str
):

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    results = search_products(
        search,
        location
    )


    # --------------------------------------------------------
    # Product not found
    # --------------------------------------------------------

    if not results:

        return {

            "success": False,

            "product_found": False,

            "available_anywhere": False,

            "search": search,

            "location": location,

            "message": (
                "No matching product was found."
            ),

            "prices": [],

        }


    # --------------------------------------------------------
    # Find available products
    # --------------------------------------------------------

    available_products = (
        get_available_products(
            results
        )
    )


    # --------------------------------------------------------
    # Product exists but unavailable everywhere
    # --------------------------------------------------------

    if not available_products:

        return {

            "success": True,

            "product_found": True,

            "available_anywhere": False,

            "search": search,

            "location": location,

            "product": {

                "name": results[0]["name"],

                "brand": results[0]["brand"],

                "quantity": results[0]["quantity"],

                "unit": results[0]["unit"],

            },

            "message": (
                "Product was found, "
                "but it is currently "
                "unavailable on all platforms."
            ),

            "prices": [

                {

                    "platform": item["platform"],

                    "price": item["price"],

                    "available": False,

                    "location": item["location"],

                    "checked_at": item["checked_at"],

                }

                for item in results

            ],

        }


    # --------------------------------------------------------
    # Find cheapest AVAILABLE platform
    # --------------------------------------------------------

    cheapest = find_cheapest_available(
        results
    )


    # --------------------------------------------------------
    # Highest available price
    # --------------------------------------------------------

    highest_available_price = max(

        item["price"]

        for item in available_products

    )


    # --------------------------------------------------------
    # Saving
    # --------------------------------------------------------

    saving = (

        highest_available_price
        - cheapest["price"]

    )


    # --------------------------------------------------------
    # Platform results
    # --------------------------------------------------------

    prices = []


    for item in results:

        prices.append({

            "platform": item["platform"],

            "price": item["price"],

            "available": item["available"],

            "location": item["location"],

            "checked_at": item["checked_at"],

        })


    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {

        "success": True,

        "product_found": True,

        "available_anywhere": True,

        "search": search,

        "location": location,

        "product": {

            "name": cheapest["name"],

            "brand": cheapest["brand"],

            "quantity": cheapest["quantity"],

            "unit": cheapest["unit"],

        },

        "prices": prices,

        "cheapest": {

            "platform": cheapest["platform"],

            "price": cheapest["price"],

            "available": True,

            "location": cheapest["location"],

            "checked_at": cheapest["checked_at"],

        },

        "maximum_saving": saving,

    }