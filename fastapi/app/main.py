from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.databases import sqlite_db
from app.services.seed_data import seed_database
from app.routers import aar


@asynccontextmanager
async def lifespan(app: FastAPI):
    await sqlite_db.init_db()
    await seed_database()
    yield
    await sqlite_db.close_db()


app = FastAPI(title="AAR Admin API", version="0.1.0", lifespan=lifespan)
app.include_router(aar.router)


@app.get("/healthCheck")
async def health_check():
    healthy = await sqlite_db.check_health()
    return {"status": "OK" if healthy else "ERROR"}


@app.get("/version")
async def version():
    return {"version": "0.1.0"}
