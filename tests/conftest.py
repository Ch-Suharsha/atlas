from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Customer, Order


@pytest.fixture()
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all(
        [
            Customer(
                id="customer-1",
                name="Alice",
                email="alice@example.com",
                tier="standard",
                member_since=datetime(2025, 1, 1),
            ),
            Customer(
                id="customer-2",
                name="Bob",
                email="bob@example.com",
                tier="standard",
                member_since=datetime(2025, 1, 1),
            ),
        ]
    )
    session.add_all(
        [
            Order(
                id="ORD-ALICE",
                customer_id="customer-1",
                status="Shipped",
                carrier="UPS",
                tracking="TRACK-1",
                eta="2026-05-08",
                items=[{"title": "Headphones", "qty": 1}],
                total_cents=2500,
                currency="USD",
                created_at=datetime(2026, 1, 1),
            ),
            Order(
                id="ORD-BOB",
                customer_id="customer-2",
                status="processing",
                items=[{"title": "Keyboard", "qty": 1}],
                total_cents=1500,
                currency="USD",
                created_at=datetime(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.close()
