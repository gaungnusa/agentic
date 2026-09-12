from fastapi import APIRouter, HTTPException, Query
from app.core.database import get_pool
from app.engine.semantic_search import search_catalog_semantic
from typing import List, Dict, Any, Optional
import json

router = APIRouter(prefix="/api/v1/replica", tags=["ERP Read-Replica Explorer"])

def check_db_pool():
    return get_pool()

@router.get("/master-price/{entity_code}")
async def list_replica_master_prices(entity_code: str):
    pool = check_db_pool()
    if pool is None:
        from app.api.chat import IN_MEMORY_MASTER_PRICE
        filtered = [p for p in IN_MEMORY_MASTER_PRICE if p.get("entity_code") == entity_code or entity_code == "ALL"]
        return filtered or IN_MEMORY_MASTER_PRICE

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT part_number, description, unit_cost, currency, moq_threshold, valid_until, entity_code
            FROM mock_master_price
            WHERE entity_code = $1
            ORDER BY part_number ASC;
            """,
            entity_code
        )
    return [
        {
            "part_number": r["part_number"],
            "description": r["description"],
            "unit_cost": float(r["unit_cost"]) if r["unit_cost"] is not None else None,
            "currency": r["currency"],
            "moq_threshold": r["moq_threshold"],
            "valid_until": r["valid_until"].isoformat() if r["valid_until"] else None,
            "entity_code": r["entity_code"]
        }
        for r in rows
    ]

@router.get("/catalog/semantic-search")
async def semantic_search_catalog(
    q: str = Query(..., description="Query pencarian semantik (misal: 'transceiver 10g optik')"),
    entity_code: str = Query("ALL", description="Kode entitas (SG, VN, KR, IN, JP, atau ALL)"),
    limit: int = Query(5, ge=1, le=20),
    min_score: float = Query(0.15, ge=0.0, le=1.0)
):
    """
    Pencarian semantik katalog suku cadang menggunakan PostgreSQL pgvector cosine distance.
    Menghitung kemiripan vektor 384 dimensi terhadap part_number dan description.
    """
    pool = check_db_pool()
    if pool is None:
        from app.api.chat import IN_MEMORY_MASTER_PRICE
        query = q.lower()
        matches = [
            {**p, "similarity_score": 0.85}
            for p in IN_MEMORY_MASTER_PRICE
            if (p.get("entity_code") == entity_code or entity_code == "ALL") and (query in p["part_number"].lower() or query in p["description"].lower())
        ]
        return matches[:limit] if matches else [{**p, "similarity_score": 0.5} for p in IN_MEMORY_MASTER_PRICE[:limit]]

    results = await search_catalog_semantic(
        pool=pool,
        query=q,
        entity_code=entity_code,
        limit=limit,
        min_similarity=min_score
    )
    return results

@router.get("/borrowed-stock/{entity_code}")
async def list_replica_borrowed_stock(entity_code: str):
    pool = check_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT loan_ref, partner_name, part_number, qty, borrowed_date, max_loan_days, status, entity_code
            FROM mock_borrowed_stock
            WHERE entity_code = $1
            ORDER BY borrowed_date DESC;
            """,
            entity_code
        )
    return [
        {
            "loan_ref": r["loan_ref"],
            "partner_name": r["partner_name"],
            "part_number": r["part_number"],
            "qty": r["qty"],
            "borrowed_date": r["borrowed_date"].isoformat() if r["borrowed_date"] else None,
            "max_loan_days": r["max_loan_days"],
            "status": r["status"],
            "entity_code": r["entity_code"]
        }
        for r in rows
    ]

@router.get("/sales-orders/{entity_code}")
async def list_replica_sales_orders(entity_code: str):
    pool = check_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT so_number, customer_name, part_number, ordered_qty, selling_price, order_value, rdd_target, eta_delivery, status, entity_code
            FROM mock_sales_orders
            WHERE entity_code = $1
            ORDER BY rdd_target ASC;
            """,
            entity_code
        )
    return [
        {
            "so_number": r["so_number"],
            "customer_name": r["customer_name"],
            "part_number": r["part_number"],
            "ordered_qty": r["ordered_qty"],
            "selling_price": float(r["selling_price"]) if r["selling_price"] is not None else None,
            "order_value": float(r["order_value"]) if r["order_value"] is not None else None,
            "rdd_target": r["rdd_target"].isoformat() if r["rdd_target"] else None,
            "eta_delivery": r["eta_delivery"].isoformat() if r["eta_delivery"] else None,
            "status": r["status"],
            "entity_code": r["entity_code"]
        }
        for r in rows
    ]

@router.get("/purchase-orders/{entity_code}")
async def list_replica_purchase_orders(entity_code: str):
    pool = check_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT po_number, so_number, supplier_name, part_number, ordered_qty, po_cost_price, 
                   supplier_moq, tier2_cost_price, expected_qty, scanned_qty, damaged_qty, status, entity_code
            FROM mock_purchase_orders
            WHERE entity_code = $1
            ORDER BY po_number ASC;
            """,
            entity_code
        )
    return [
        {
            "po_number": r["po_number"],
            "so_number": r["so_number"],
            "supplier_name": r["supplier_name"],
            "part_number": r["part_number"],
            "ordered_qty": r["ordered_qty"],
            "po_cost_price": float(r["po_cost_price"]) if r["po_cost_price"] is not None else None,
            "supplier_moq": r["supplier_moq"],
            "tier2_cost_price": float(r["tier2_cost_price"]) if r["tier2_cost_price"] is not None else None,
            "expected_qty": r["expected_qty"],
            "scanned_qty": r["scanned_qty"],
            "damaged_qty": r["damaged_qty"],
            "status": r["status"],
            "entity_code": r["entity_code"]
        }
        for r in rows
    ]

@router.get("/vendors/{entity_code}")
async def list_replica_vendors(entity_code: str):
    pool = check_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT vendor_code, vendor_name, country, on_time_rate, quality_rate, price_variance_pct, entity_code
            FROM mock_vendors
            WHERE entity_code = $1
            ORDER BY vendor_name ASC;
            """,
            entity_code
        )
    return [
        {
            "vendor_code": r["vendor_code"],
            "vendor_name": r["vendor_name"],
            "country": r["country"],
            "on_time_rate": float(r["on_time_rate"]) if r["on_time_rate"] is not None else None,
            "quality_rate": float(r["quality_rate"]) if r["quality_rate"] is not None else None,
            "price_variance_pct": float(r["price_variance_pct"]) if r["price_variance_pct"] is not None else None,
            "entity_code": r["entity_code"]
        }
        for r in rows
    ]

@router.get("/bank-transactions/{entity_code}")
async def list_replica_bank_transactions(entity_code: str):
    pool = check_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT txn_ref, bank_name, remittance_currency, remittance_amount, book_rate, settle_rate, target_invoices, entity_code
            FROM mock_bank_transactions
            WHERE entity_code = $1
            ORDER BY txn_ref ASC;
            """,
            entity_code
        )
    return [
        {
            "txn_ref": r["txn_ref"],
            "bank_name": r["bank_name"],
            "remittance_currency": r["remittance_currency"],
            "remittance_amount": float(r["remittance_amount"]) if r["remittance_amount"] is not None else None,
            "book_rate": float(r["book_rate"]) if r["book_rate"] is not None else None,
            "settle_rate": float(r["settle_rate"]) if r["settle_rate"] is not None else None,
            "target_invoices": json.loads(r["target_invoices"]) if isinstance(r["target_invoices"], str) else (r["target_invoices"] or []),
            "entity_code": r["entity_code"]
        }
        for r in rows
    ]

@router.get("/cash-position/{entity_code}")
async def get_replica_cash_position(entity_code: str):
    pool = check_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT entity_code, period_ref, current_cash, weekly_burn_rate, loan_due_7days, updated_at
            FROM mock_entity_cash
            WHERE entity_code = $1;
            """,
            entity_code
        )
    if not row:
        return {"entity_code": entity_code, "status": "NOT_FOUND", "current_cash": 0.0, "weekly_burn_rate": 0.0, "loan_due_7days": 0.0}
    return {
        "entity_code": row["entity_code"],
        "period_ref": row["period_ref"],
        "current_cash": float(row["current_cash"]) if row["current_cash"] is not None else 0.0,
        "weekly_burn_rate": float(row["weekly_burn_rate"]) if row["weekly_burn_rate"] is not None else 0.0,
        "loan_due_7days": float(row["loan_due_7days"]) if row["loan_due_7days"] is not None else 0.0,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
    }
