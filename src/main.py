from fastapi import FastAPI

from src.api.v1.auth import router as auth_router


app = FastAPI(
    title="ReelNest API",
    description="Online Cinema backend",
    version="1.0.0",
)

app.include_router(auth_router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to ReelNest!"}
