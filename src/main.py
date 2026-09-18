from fastapi import FastAPI

from src.api.v1.auth import router as auth_router
from src.api.v1.cart import router as cart_router
from src.api.v1.movies import router as movies_router
from src.api.v1.movie_interactions import router as movie_interactions_router


app = FastAPI(
    title="ReelNest API",
    description="Online Cinema backend",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(movie_interactions_router)
app.include_router(cart_router)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Welcome to ReelNest!"}
