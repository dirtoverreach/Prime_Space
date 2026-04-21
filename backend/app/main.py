from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    import app.models  # noqa: F401 — ensure all models are registered
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Prime Space",
    description="Multi-vendor network management — Juniper + Cisco",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1 import devices, topology, configs, monitoring, alerts, commands

app.include_router(devices.router, prefix="/api/v1")
app.include_router(topology.router, prefix="/api/v1")
app.include_router(configs.router, prefix="/api/v1")
app.include_router(monitoring.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(commands.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
