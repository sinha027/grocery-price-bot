from .base import BaseProvider, ProductResult
from .bigbasket import BigBasketProvider
from .jiomart import JioMartProvider


PROVIDERS = [
    JioMartProvider(),
    BigBasketProvider(),
]


__all__ = [
    "BaseProvider",
    "ProductResult",
    "JioMartProvider",
    "BigBasketProvider",
    "PROVIDERS",
]