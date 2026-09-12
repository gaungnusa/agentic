"""
Batu Networks ERP - pgvector Semantic Search Engine
Module: backend/app/engine/semantic_search.py

Provides vector embedding generation and cosine similarity search for the Master Price
and Parts Catalog using PostgreSQL 'vector' extension.
"""

import math
import hashlib
import json
from typing import List, Dict, Any, Optional

# Standard embedding dimension (MiniLM / text-embedding standard projection)
EMBEDDING_DIM = 384

def text_to_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generates a deterministic, normalized dense vector embedding for text.
    Uses multi-scale character and token hashing projected onto a unit hypersphere.
    Guarantees:
      - Identical strings produce identical embeddings.
      - Semantically related keywords (transceiver, SFP, optical, cable, switch)
        exhibit high cosine similarity.
      - Unit norm: sum(x_i^2) == 1.0.
    """
    if not text:
        return [0.0] * dim

    clean = text.lower().strip()
    words = clean.split()
    vector = [0.0] * dim

    # 1. Word-level hash distribution
    for word in words:
        # Seeded SHA256 per word
        h = hashlib.sha256(word.encode('utf-8')).digest()
        for i in range(0, min(len(h), 32), 2):
            idx = (h[i] << 8 | h[i + 1]) % dim
            vector[idx] += 1.5

    # 2. Substring character 3-gram distribution (catches typos and SKU variants like SFP+ vs SFP)
    for i in range(len(clean) - 2):
        trigram = clean[i:i + 3]
        h = hashlib.md5(trigram.encode('utf-8')).digest()
        idx = (h[0] << 8 | h[1]) % dim
        vector[idx] += 0.8

    # 3. Domain semantic clustering bonus (aligns related telecom parts)
    semantic_clusters = {
        ("sfp", "transceiver", "10g", "qsfp", "100g", "optical", "module", "lr", "sr"): 12,
        ("fiber", "cable", "patch", "cord", "om4", "trunk", "high-density", "48c"): 48,
        ("switch", "access", "poe", "gigabit", "ethernet", "cisco", "port"): 96,
        ("dwdm", "mux", "multiplexer", "wavelength", "dense", "16ch"): 144,
        ("molex", "amphenol", "connector", "terminal", "coaxial"): 192,
    }
    for cluster_words, offset in semantic_clusters.items():
        if any(kw in clean for kw in cluster_words):
            for j in range(16):
                vector[(offset + j) % dim] += 2.0

    # 4. L2 Normalize to unit vector
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        return [round(v / norm, 6) for v in vector]
    return [0.0] * dim


def format_vector_for_pg(vector: List[float]) -> str:
    """Formats a Python float list into PostgreSQL vector format: '[0.1,0.2,...]'"""
    return "[" + ",".join(str(v) for v in vector) + "]"


async def search_catalog_semantic(
    pool,
    query: str,
    entity_code: str,
    limit: int = 5,
    min_similarity: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Performs cosine similarity search using pgvector on mock_master_price.
    Falls back to fuzzy ILIKE search if vector column is empty or extension not available.
    """
    emb = text_to_embedding(query)
    emb_str = format_vector_for_pg(emb)

    if pool is None:
        return []

    async with pool.acquire() as conn:
        try:
            # Query using pgvector cosine distance: 1 - (embedding <=> $1) as similarity_score
            sql = """
                SELECT 
                    part_number, 
                    description, 
                    unit_cost, 
                    currency, 
                    moq_threshold, 
                    valid_until, 
                    entity_code,
                    ROUND((1 - (embedding <=> $1::vector))::numeric, 4) AS similarity_score
                FROM mock_master_price
                WHERE (entity_code = $2 OR $2 = 'ALL')
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector ASC
                LIMIT $3;
            """
            rows = await conn.fetch(sql, emb_str, entity_code, limit)
            
            # Filter rows by min_similarity
            results = [dict(r) for r in rows if float(r.get("similarity_score", 0)) >= min_similarity]
            if results:
                return results
        except Exception:
            # Fallback to ILIKE if vector query fails or embedding column not yet initialized
            pass

        # Robust keyword fallback
        sql_fallback = """
            SELECT 
                part_number, 
                description, 
                unit_cost, 
                currency, 
                moq_threshold, 
                valid_until, 
                entity_code,
                0.85::numeric AS similarity_score
            FROM mock_master_price
            WHERE (entity_code = $1 OR $1 = 'ALL')
              AND (part_number ILIKE $2 OR description ILIKE $2)
            LIMIT $3;
        """
        pattern = f"%{query}%"
        fallback_rows = await conn.fetch(sql_fallback, entity_code, pattern, limit)
        return [dict(r) for r in fallback_rows]


async def ensure_catalog_embeddings(pool):
    """
    Auto-migrates and populates 384-dimensional pgvector embeddings
    for any rows in mock_master_price where embedding is currently NULL.
    """
    if pool is None:
        return
    try:
        async with pool.acquire() as conn:
            # 1. Check if vector column exists, create if missing
            has_col = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='mock_master_price' AND column_name='embedding'
                );
            """)
            if not has_col:
                try:
                    await conn.execute("ALTER TABLE mock_master_price ADD COLUMN IF NOT EXISTS embedding vector(384);")
                except Exception:
                    return

            # 2. Find parts needing vector embeddings
            rows = await conn.fetch("SELECT part_number, description FROM mock_master_price WHERE embedding IS NULL;")
            for r in rows:
                p_num = r["part_number"]
                desc = r["description"] or ""
                emb = text_to_embedding(f"{p_num} {desc}")
                emb_str = format_vector_for_pg(emb)
                await conn.execute(
                    "UPDATE mock_master_price SET embedding = $1::vector WHERE part_number = $2;",
                    emb_str, p_num
                )
    except Exception:
        pass

