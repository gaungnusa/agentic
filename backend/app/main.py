from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db, get_pool
from app.engine.semantic_search import ensure_catalog_embeddings
from app.api.agents import router as agents_router
from app.api.hitl import router as hitl_router
from app.api.replica import router as replica_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router

app = FastAPI(
    title="Batu Networks ERP - Agentic AI Engine",
    version="1.0.0",
    description="Deterministic Backend & Cognitive RAG Gateway for Enterprise ERP BRD v10.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.ENVIRONMENT != "development" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()
    pool = get_pool()
    if pool:
        await ensure_catalog_embeddings(pool)

@app.on_event("shutdown")
async def shutdown():
    await close_db()

app.include_router(agents_router)
app.include_router(hitl_router)
app.include_router(replica_router)
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ONLINE", "version": "1.0.0", "legal_entities": ["SG", "VN", "KR", "IN", "JP"]}