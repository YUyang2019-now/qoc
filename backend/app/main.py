import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import hash_password
from .config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USER
from .db import Base, SessionLocal, engine, upgrade_schema
from .models import Setting, User
from .routes import router
from .services.cleanup import run_cleanup_once

logger = logging.getLogger(__name__)


def seed_defaults():
    db = SessionLocal()
    try:
        if not db.query(User).first():
            db.add(
                User(
                    username=DEFAULT_ADMIN_USER,
                    password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                )
            )
        if not db.get(Setting, "low_stock_threshold"):
            db.add(Setting(key="low_stock_threshold", value="10"))
        if not db.get(Setting, "snapshot_retention_days"):
            db.add(Setting(key="snapshot_retention_days", value="60"))
        db.commit()
    finally:
        db.close()


async def cleanup_loop():
    while True:
        try:
            deleted, cutoff = await asyncio.to_thread(run_cleanup_once)
            if deleted:
                logger.info("已清理 %s 条 %s 之前的快照", deleted, cutoff)
        except Exception:
            logger.exception("自动清理快照失败")
        await asyncio.sleep(24 * 3600)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    upgrade_schema()
    seed_defaults()
    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="QOC 商品管理系统", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


@app.exception_handler(StarletteHTTPException)
async def spa_fallback(request: Request, exc: StarletteHTTPException):
    if (
        exc.status_code == 404
        and dist.exists()
        and not request.url.path.startswith("/api")
    ):
        index = dist / "index.html"
        if index.exists():
            return FileResponse(index)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
