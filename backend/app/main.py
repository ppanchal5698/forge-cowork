from fastapi import FastAPI

app = FastAPI(title="Forge Cowork API")


@app.get("/health")
def health():
    return {"status": "ok"}
