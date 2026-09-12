import asyncpg
from app.core.config import settings

db_pool = None

async def init_db():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=10,
            command_timeout=5.0,
            ssl=False
        )
        print("INFO: Connected to PostgreSQL database pool.")
    except Exception as e:
        print(f"WARNING: Database connection failed ({e}). Starting FastAPI in graceful mode.")
        db_pool = None

async def close_db():
    global db_pool
    if db_pool:
        await db_pool.close()

def get_pool():
    return db_pool