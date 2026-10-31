import json
import os
from uuid import UUID

import requests
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.billing_agent import create_renewal_invoices
from app.agents.lifecycle_agent import find_expiring_subscriptions, subscription_context
from app.agents.payment_agent import explain_unmatched_payments
from app.models.log import AgentLog
from app.models.user import User

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
ALLOWED_INTENTS = {"find_expiring_subscriptions", "generate_renewal_invoices", "explain_unmatched_payments", "unsupported"}


def _classify_request(text: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(503, "Natural-language orchestration is not configured")
    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": (
                        "Classify the request for a subscription billing system. Return JSON only with keys "
                        "intent and days. intent must be find_expiring_subscriptions, "
                        "generate_renewal_invoices, explain_unmatched_payments, or unsupported. "
                        "days must be an integer 1..365 (use 7 when irrelevant). "
                        "Use explain_unmatched_payments for requests about unmatched/unreconciled bank payments. "
                        "Use generate_renewal_invoices only when invoice creation is explicitly requested. "
                        "Never return actions, code, SQL, IDs, or additional keys."
                    )},
                    {"role": "user", "content": text},
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        result = json.loads(content)
        intent = result.get("intent")
        days = result.get("days")
        if intent not in ALLOWED_INTENTS or isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 365:
            raise ValueError("Invalid intent response")
        return {"intent": intent, "days": days}
    except requests.RequestException as exc:
        raise HTTPException(502, "The language model service is temporarily unavailable") from exc
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(502, "Could not safely interpret the request") from exc


def create_plan(db: Session, user: User, text: str) -> dict:
    parsed = _classify_request(text)
    intent = parsed["intent"]
    subscriptions = find_expiring_subscriptions(db, parsed["days"]) if intent in ("find_expiring_subscriptions", "generate_renewal_invoices") else []
    candidates = [subscription_context(db, sub) for sub in subscriptions]
    reconciliation_items = explain_unmatched_payments(db) if intent == "explain_unmatched_payments" else []
    summaries = {
        "find_expiring_subscriptions": f"Found {len(candidates)} subscription(s) expiring within {parsed['days']} days.",
        "generate_renewal_invoices": f"Prepared renewal invoices for {len(candidates)} subscription(s); confirm to create draft invoices.",
        "explain_unmatched_payments": f"Found {len(reconciliation_items)} unresolved bank transaction(s). Explanations use recorded reconciliation evidence.",
        "unsupported": "I can help find expiring subscriptions, prepare renewal invoices, or explain unmatched payments. This request does not match a supported workflow.",
    }
    summary = summaries[intent]
    routed_agents = {
        "find_expiring_subscriptions": ["lifecycle"],
        "generate_renewal_invoices": ["lifecycle", "billing"],
        "explain_unmatched_payments": ["payment"],
        "unsupported": [],
    }[intent]
    plan_steps = {
        "find_expiring_subscriptions": ["Find subscriptions ending within the requested window", "Return matching subscription and plan details"],
        "generate_renewal_invoices": ["Find subscriptions ending within the requested window", "Check for an existing renewal invoice", "Create draft invoices after confirmation"],
        "explain_unmatched_payments": ["Load unresolved reconciliation entries", "Explain their status using recorded match notes"],
        "unsupported": [],
    }[intent]
    task = AgentLog(
        agent_name="orchestrator",
        action=intent,
        input_context={"user_id": str(user.id), "days": parsed["days"]},
        output_result={"intent": intent, "days": parsed["days"], "candidate_ids": [str(sub.id) for sub in subscriptions]},
        status="awaiting_confirmation" if intent == "generate_renewal_invoices" else "unsupported" if intent == "unsupported" else "completed",
    )
    db.add(task)
    db.flush()
    for agent_name in routed_agents:
        db.add(AgentLog(
            agent_name=f"{agent_name}_agent",
            action=intent,
            input_context={"user_id": str(user.id), "task_id": str(task.id), "days": parsed["days"]},
            output_result={"candidate_count": len(candidates) if agent_name != "payment" else len(reconciliation_items)},
            status="awaiting_confirmation" if agent_name == "billing" and intent == "generate_renewal_invoices" else "success",
        ))
    db.commit()
    db.refresh(task)
    return {
        "task_id": task.id,
        "intent": intent,
        "summary": summary,
        "requires_confirmation": intent == "generate_renewal_invoices",
        "candidates": candidates,
        "reconciliation_items": reconciliation_items,
        "agents": routed_agents,
        "steps": plan_steps,
    }


def execute_plan(db: Session, user: User, task_id: UUID) -> dict:
    task = db.scalar(select(AgentLog).where(AgentLog.id == task_id).with_for_update())
    if task is None or task.agent_name != "orchestrator":
        raise HTTPException(404, "Orchestration task not found")
    if not task.input_context or task.input_context.get("user_id") != str(user.id):
        raise HTTPException(403, "This task belongs to another user")
    if not task.output_result or task.output_result.get("intent") != "generate_renewal_invoices":
        raise HTTPException(409, "This task has no financial action to execute")
    if task.status == "completed":
        output = task.output_result or {}
        return {"task_id": task.id, "status": "completed", "created_count": output.get("created_count", 0), "skipped_count": output.get("skipped_count", 0), "invoice_ids": output.get("invoice_ids", []), "message": "This task was already completed; returning its original result."}
    if task.status != "awaiting_confirmation":
        raise HTTPException(409, "This task is not awaiting confirmation")
    ids = [UUID(value) for value in task.output_result.get("candidate_ids", [])]
    invoice_ids, skipped = create_renewal_invoices(db, ids)
    result = {"intent": task.output_result["intent"], "candidate_ids": task.output_result.get("candidate_ids", []), "invoice_ids": [str(value) for value in invoice_ids], "created_count": len(invoice_ids), "skipped_count": skipped}
    task.output_result = result
    task.status = "completed"
    task.error_message = None
    db.add(AgentLog(
        agent_name="billing_agent",
        action="create_renewal_invoices",
        input_context={"user_id": str(user.id), "task_id": str(task.id), "candidate_count": len(ids)},
        output_result={"invoice_ids": result["invoice_ids"], "created_count": len(invoice_ids), "skipped_count": skipped},
        status="success",
    ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"task_id": task.id, "status": task.status, "created_count": len(invoice_ids), "skipped_count": skipped, "invoice_ids": invoice_ids, "message": f"Created {len(invoice_ids)} draft renewal invoice(s); skipped {skipped}."}
