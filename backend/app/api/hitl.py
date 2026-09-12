from fastapi import APIRouter, HTTPException, Depends
from app.schemas.agent_payloads import HITLDecisionRequest
from app.core.database import get_pool
from app.core.auth import get_current_user, require_role_for_agent
from app.engine.dispatcher import dispatch_approved_action
from typing import Dict, Any
import json
import uuid

router = APIRouter(prefix="/api/v1/hitl", tags=["Human in the Loop"])

def check_db_pool():
    return get_pool()

@router.get("/queue/{entity_code}")
async def list_pending_drafts(entity_code: str):
    pool = check_db_pool()
    if pool is None:
        from app.api.chat import IN_MEMORY_DRAFTS
        filtered = [
            d for d in IN_MEMORY_DRAFTS 
            if (d.get("entity_code") == entity_code or entity_code == "ALL") and d.get("status") == "PENDING"
        ]
        return [
            {
                "id": str(d["id"]),
                "agent_id": d["agent_id"],
                "module": d.get("module_code", "GEN"),
                "ref_doc": d.get("reference_doc", "REF"),
                "payload": d.get("deterministic_payload", {}),
                "narrative": d.get("llm_draft_narrative", ""),
                "created_at": d.get("created_at")
            }
            for d in filtered
        ]

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, agent_id, entity_code, module_code, reference_doc, 
                   deterministic_payload, llm_draft_narrative, created_at 
            FROM draft_agent_actions 
            WHERE entity_code = $1 AND status = 'PENDING'
            ORDER BY created_at DESC;
            """,
            entity_code
        )
    result = []
    for r in rows:
        payload_raw = r["deterministic_payload"]
        if isinstance(payload_raw, str):
            try:
                payload_obj = json.loads(payload_raw)
            except Exception:
                payload_obj = {}
        else:
            payload_obj = payload_raw or {}

        result.append({
            "id": str(r["id"]),
            "agent_id": r["agent_id"],
            "module": r["module_code"],
            "ref_doc": r["reference_doc"],
            "payload": payload_obj,
            "narrative": r["llm_draft_narrative"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None
        })
    return result

@router.post("/decision")
async def commit_hitl_decision(
    req: HITLDecisionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    pool = check_db_pool()
    operator_identity = req.operator_id or current_user.get("username", "system_operator")
    final_status = "APPROVED" if req.decision == "APPROVE" else ("EDITED" if req.decision == "EDIT" else "DISCARDED")
    
    if pool is None:
        from app.api.chat import IN_MEMORY_DRAFTS, IN_MEMORY_AUDIT
        draft = next((d for d in IN_MEMORY_DRAFTS if str(d["id"]) == req.draft_action_id), None)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft action tidak ditemukan.")
        
        require_role_for_agent(draft["agent_id"], current_user)
        draft["status"] = final_status
        draft["reviewed_by"] = operator_identity
        
        final_text = req.modified_narrative if req.decision == "EDIT" else draft.get("llm_draft_narrative", "")
        dispatch_result = {"status": "DISCARDED_NO_ACTION"}
        if final_status in ["APPROVED", "EDITED"]:
            dispatch_result = await dispatch_approved_action(
                agent_id=draft["agent_id"],
                entity_code=draft["entity_code"],
                reference_doc=draft["reference_doc"],
                payload=draft.get("deterministic_payload", {}),
                final_narrative=final_text
            )
            
        IN_MEMORY_AUDIT.insert(0, {
            "id": str(uuid.uuid4()),
            "draft_action_id": req.draft_action_id,
            "operator_id": operator_identity,
            "entity_code": draft["entity_code"],
            "event_action": final_status,
            "original_text": draft.get("llm_draft_narrative", ""),
            "final_dispatched_text": final_text,
            "execution_result": dispatch_result,
            "agent_id": draft["agent_id"],
            "module_code": draft.get("module_code", "N/A"),
            "reference_doc": draft.get("reference_doc", "N/A"),
            "created_at": datetime.now().isoformat()
        })
        
        return {
            "status": "PROCESSED",
            "action_taken": final_status,
            "reviewed_by": operator_identity,
            "dispatch_details": dispatch_result,
            "message": f"Draf {req.draft_action_id} diproses oleh {operator_identity} dan tercatat di audit trail (in-memory)."
        }

    try:
        target_uuid = uuid.UUID(req.draft_action_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Format draft_action_id tidak valid (harus UUID).")

    async with pool.acquire() as conn:
        draft = await conn.fetchrow("SELECT * FROM draft_agent_actions WHERE id = $1", target_uuid)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft action tidak ditemukan.")

        # Enforce RBAC Role Check for this agent
        require_role_for_agent(draft["agent_id"], current_user)

        final_text = req.modified_narrative if req.decision == "EDIT" else draft["llm_draft_narrative"]

        payload_raw = draft["deterministic_payload"]
        if isinstance(payload_raw, str):
            try:
                payload_data = json.loads(payload_raw)
            except Exception:
                payload_data = {}
        else:
            payload_data = payload_raw or {}

        # 1. Panggil Action Dispatcher jika disetujui
        dispatch_result = {"status": "DISCARDED_NO_ACTION"}
        if final_status in ["APPROVED", "EDITED"]:
            dispatch_result = await dispatch_approved_action(
                agent_id=draft["agent_id"],
                entity_code=draft["entity_code"],
                reference_doc=draft["reference_doc"],
                payload=payload_data,
                final_narrative=final_text
            )

        # 2. Update status staging table
        await conn.execute(
            """
            UPDATE draft_agent_actions 
            SET status = $1, reviewed_by = $2, reviewed_at = NOW(), updated_at = NOW()
            WHERE id = $3
            """,
            final_status, operator_identity, target_uuid
        )

        # 3. Catat riwayat lengkap ke audit trail log yang immutable
        await conn.execute(
            """
            INSERT INTO audit_trail_logs 
            (draft_action_id, operator_id, entity_code, event_action, original_text, final_dispatched_text, execution_result)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            target_uuid, operator_identity, draft["entity_code"], final_status,
            draft["llm_draft_narrative"], final_text, json.dumps(dispatch_result)
        )

    return {
        "status": "PROCESSED",
        "action_taken": final_status,
        "reviewed_by": operator_identity,
        "dispatch_details": dispatch_result,
        "message": f"Draf {req.draft_action_id} diproses oleh {operator_identity} dan tercatat di audit trail."
    }

@router.get("/audit/{entity_code}")
async def list_audit_trail_logs(entity_code: str, limit: int = 50):
    pool = check_db_pool()
    if pool is None:
        from app.api.chat import IN_MEMORY_AUDIT
        filtered = [
            a for a in IN_MEMORY_AUDIT
            if a.get("entity_code") == entity_code or entity_code == "ALL"
        ]
        return [
            {
                "id": str(a.get("id", "")),
                "draft_action_id": a.get("draft_action_id"),
                "operator_id": a.get("operator_id", a.get("operator", "system")),
                "entity_code": a.get("entity_code", entity_code),
                "event_action": a.get("event_action", a.get("action", "APPROVED")),
                "original_text": a.get("original_text", ""),
                "final_dispatched_text": a.get("final_dispatched_text", ""),
                "execution_result": a.get("execution_result", {}),
                "agent_id": a.get("agent_id", a.get("agent", "agent_1")),
                "module_code": a.get("module_code", a.get("module", "N/A")),
                "reference_doc": a.get("reference_doc", a.get("ref_doc", "N/A")),
                "created_at": a.get("created_at", a.get("time"))
            }
            for a in filtered[:limit]
        ]
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                a.id,
                a.draft_action_id,
                a.operator_id,
                a.entity_code,
                a.event_action,
                a.original_text,
                a.final_dispatched_text,
                a.execution_result,
                a.created_at,
                d.agent_id,
                d.module_code,
                d.reference_doc
            FROM audit_trail_logs a
            LEFT JOIN draft_agent_actions d ON a.draft_action_id = d.id
            WHERE a.entity_code = $1
            ORDER BY a.created_at DESC
            LIMIT $2;
            """,
            entity_code, limit
        )
    return [
        {
            "id": str(r["id"]),
            "draft_action_id": str(r["draft_action_id"]) if r["draft_action_id"] else None,
            "operator_id": r["operator_id"],
            "entity_code": r["entity_code"],
            "event_action": r["event_action"],
            "original_text": r["original_text"],
            "final_dispatched_text": r["final_dispatched_text"],
            "execution_result": json.loads(r["execution_result"]) if r["execution_result"] and isinstance(r["execution_result"], str) else (r["execution_result"] or {}),
            "agent_id": r["agent_id"] or "system",
            "module_code": r["module_code"] or "N/A",
            "reference_doc": r["reference_doc"] or "N/A",
            "created_at": r["created_at"].isoformat() if r["created_at"] else None
        }
        for r in rows
    ]