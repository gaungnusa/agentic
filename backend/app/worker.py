import asyncio
import json
import logging
from datetime import date, timedelta
from app.core.database import init_db, close_db, get_pool
from app.engine.llm_synthesizer import generate_grounded_draft
from app.engine.deterministic import compute_agent7_loan_maturity

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("erp_worker")

POLL_INTERVAL_SECONDS = 900  # 15 menit

async def scan_agent4_expiring_prices(pool):
    """Agent 4: Memindai master price yang akan kedaluwarsa dalam 30 hari (H-30)"""
    h30_date = date.today() + timedelta(days=30)
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT part_number, description, unit_cost, currency, valid_until, entity_code
            FROM mock_master_price
            WHERE valid_until <= $1;
            """,
            h30_date
        )

        for r in records:
            exists = await conn.fetchval(
                """
                SELECT id FROM draft_agent_actions
                WHERE agent_id = 'agent_4' AND reference_doc = $1 AND status = 'PENDING';
                """,
                r["part_number"]
            )
            if not exists:
                payload = {
                    "part_number": r["part_number"],
                    "current_cost": float(r["unit_cost"]),
                    "currency": r["currency"],
                    "valid_until": r["valid_until"].isoformat(),
                    "recommended_inflation_adjustment_pct": 2.1
                }
                draft_text = await generate_grounded_draft(
                    agent_id="agent_4",
                    entity_code=r["entity_code"],
                    deterministic_data=payload,
                    raw_context=f"Pembaruan Master Price untuk part {r['part_number']} yang jatuh tempo pada {r['valid_until']}."
                )
                await conn.execute(
                    """
                    INSERT INTO draft_agent_actions 
                    (agent_id, entity_code, module_code, reference_doc, deterministic_payload, llm_draft_narrative)
                    VALUES ($1, $2, $3, $4, $5, $6);
                    """,
                    "agent_4", r["entity_code"], "PS03", r["part_number"], json.dumps(payload), draft_text
                )
                logger.info(f"[Agent 4] Draf pembaruan harga kedaluwarsa dibuat: {r['part_number']} ({r['entity_code']})")

async def scan_agent7_stock_loans(pool):
    """Agent 7: Radar jatuh tempo peminjaman stok antar-mitra (H-5 expiry scanner)"""
    async with pool.acquire() as conn:
        # Cek apakah tabel mock_borrowed_stock tersedia
        table_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'mock_borrowed_stock'
            );
            """
        )
        if not table_exists:
            return

        records = await conn.fetch(
            """
            SELECT loan_ref, partner_name, borrowed_date, max_loan_days, entity_code
            FROM mock_borrowed_stock
            WHERE status = 'ACTIVE';
            """
        )

        for r in records:
            b_date_str = r["borrowed_date"].isoformat()
            calc = compute_agent7_loan_maturity(b_date_str, r["max_loan_days"] or 30)

            if calc["is_expiring_soon"] or calc["is_overdue"]:
                exists = await conn.fetchval(
                    """
                    SELECT id FROM draft_agent_actions
                    WHERE agent_id = 'agent_7' AND reference_doc = $1 AND status = 'PENDING';
                    """,
                    r["loan_ref"]
                )
                if not exists:
                    draft_text = await generate_grounded_draft(
                        agent_id="agent_7",
                        entity_code=r["entity_code"],
                        deterministic_data=calc,
                        raw_context=f"Pinjaman Stok {r['loan_ref']} dari {r['partner_name']}, sisa {calc['days_left']} hari."
                    )
                    await conn.execute(
                        """
                        INSERT INTO draft_agent_actions 
                        (agent_id, entity_code, module_code, reference_doc, deterministic_payload, llm_draft_narrative)
                        VALUES ($1, $2, $3, $4, $5, $6);
                        """,
                        "agent_7", r["entity_code"], "6.3_STOCK", r["loan_ref"], json.dumps(calc), draft_text
                    )
                    logger.info(f"[Agent 7] Radar H-5 terdeteksi: Pinjaman {r['loan_ref']} sisa {calc['days_left']} hari.")

async def run_scheduler():
    await init_db()
    pool = get_pool()
    logger.info("[WORKER] Scheduler aktif (Interval: 15 menit). Memulai pemantauan proaktif...")

    try:
        while True:
            try:
                if pool:
                    await scan_agent4_expiring_prices(pool)
                    await scan_agent7_stock_loans(pool)
                else:
                    logger.warning("[WORKER] Database pool belum siap. Melewatkan siklus ini.")
            except Exception as loop_err:
                logger.error(f"[WORKER] Terjadi kesalahan dalam siklus pemindaian: {loop_err}", exc_info=True)

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        logger.info("[WORKER] Scheduler dihentikan dengan aman.")
    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(run_scheduler())