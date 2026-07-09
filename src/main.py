import src.config as cfg
from fastapi import FastAPI
from src.database import init_db

app = FastAPI(title="Nodo del Clúster Distribuido", version="1.0.0")


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return {"node_id": cfg.NODE_ID, "status": "alive"}


@app.get("/health")
async def health():
    return {"node_id": cfg.NODE_ID, "role": "follower" if cfg.LEADER_ID else "leader", "status": "alive"}