from __future__ import annotations

from app.models import Order
from app.tools import (
    ToolContext,
    tool_cancel_order,
    tool_lookup_order,
    tool_process_refund,
)


def context(db, customer_id: str | None) -> ToolContext:
    return ToolContext(
        db=db,
        session_id="test-session",
        customer_id=customer_id,
        customer_email=None,
    )


def test_order_lookup_requires_identity(db):
    result = tool_lookup_order({"order_id": "ORD-ALICE"}, context(db, None))

    assert result["ok"] is False
    assert "authenticated customer" in result["error"]


def test_order_lookup_cannot_cross_customer_boundary(db):
    result = tool_lookup_order({"order_id": "ORD-BOB"}, context(db, "customer-1"))

    assert result["ok"] is False
    assert "does not belong" in result["error"]


def test_refund_is_idempotent_for_same_order_and_reason(db):
    ctx = context(db, "customer-1")

    first = tool_process_refund(
        {"order_id": "ORD-ALICE", "reason": "damaged item"}, ctx
    )
    second = tool_process_refund(
        {"order_id": "ORD-ALICE", "reason": "damaged item"}, ctx
    )

    assert first["ok"] is True
    assert second["ok"] is True
    assert second["idempotent"] is True
    assert second["refund_id"] == first["refund_id"]


def test_cancel_requires_ownership_and_keeps_processing_rule(db):
    unauthorized = tool_cancel_order(
        {"order_id": "ORD-BOB"}, context(db, "customer-1")
    )
    assert unauthorized["ok"] is False

    authorized = tool_cancel_order(
        {"order_id": "ORD-BOB"}, context(db, "customer-2")
    )
    assert authorized["ok"] is True
    assert db.get(Order, "ORD-BOB").status == "Cancelled"
