from fastapi import FastAPI

from .modules.auth.router import router as auth_router

app = FastAPI(title="Forge Cowork API")
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}
