from fastapi import FastAPI

app = FastAPI(
    title="ReelNest API",
    description="Online Cinema backend",
    version="1.0.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to ReelNest!"}
