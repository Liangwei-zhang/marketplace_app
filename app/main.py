from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db
from app.api import auth, items, chat, transaction, review
from app.websocket import chat as ws_chat


# Frontend path
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "public")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing database...")
    await init_db()
    print("Database initialized!")
    yield
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Marketplace API",
    description="Second-hand marketplace with LBS and IM",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Serve frontend static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Serve index.html for root
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(transaction.router, prefix="/api/v1")
app.include_router(review.router, prefix="/api/v1")

# WebSocket endpoint
@app.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket, room_id: int):
    await ws_chat.websocket_endpoint(websocket, room_id)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
