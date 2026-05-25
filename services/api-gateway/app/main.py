"""API Gateway placeholder — replace with routing, auth middleware, and service clients."""

from fastapi import FastAPI

app = FastAPI(
    title="Cybersec API Gateway",
    description="Placeholder gateway for local infrastructure bootstrap.",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "api-gateway"}
