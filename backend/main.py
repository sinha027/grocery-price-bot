from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.comparison import compare_product


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Grocery Price Comparison API",
    description="Compare grocery prices across multiple platforms",
    version="2.0.0",
)


# ============================================================
# CORS
# ============================================================
#
# Local development:
#   http://localhost:5173
#   http://127.0.0.1:5173
#
# Public frontend:
#   https://grocery-price-bot-frontend.onrender.com
#
# No personal information is required here.
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://grocery-price-bot-frontend.onrender.com",
        "https://grocery-price-bot-vivek-frontend.onrender.com",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Grocery Price Comparison API is running!"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# PRODUCT COMPARISON
# ============================================================

@app.get("/compare")
def compare(
    search: str,
    location: str = "",
):
    return compare_product(
        search,
        location,
    )

