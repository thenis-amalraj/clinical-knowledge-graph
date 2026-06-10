from fastapi import FastAPI

app = FastAPI(title="Clinical Knowledge Graph API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
