from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.comparison import compare_product


app = FastAPI(
    title="Grocery Price Comparison API",
    description="Compare grocery prices across multiple platforms",
    version="2.0.0"
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


@app.get("/")
def home():

    return {
        "message":
        "Grocery Price Comparison API is running!"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/compare")
def compare(
    search: str,
    location: str = ""
):

    return compare_product(
        search,
        location
    )