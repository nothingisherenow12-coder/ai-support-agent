from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func, select,delete

from app.db.database import SessionLocal
from app.models.action import Action
from app.models.ticket import Ticket
from app.services.action_executor import execute_action
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

def make_action(status="proposed"):
    action = MagicMock()
    action.id = 1
    action.action_type = "create_ticket"
    action.customer_id = 1
    action.title = "Test ticket"
    action.description = "Testing action execution"
    action.status = status
    return action


def setup_db(action):
    db = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = action
    db.execute.return_value = result
    return db


def test_unapproved_action_cannot_create_ticket():
    db = setup_db(make_action("proposed"))

    with patch(
        "app.services.action_executor.create_ticket"
    ) as mock_create:
        with pytest.raises(ValueError, match="must be approved"):
            execute_action(db=db, action_id=1)

    mock_create.assert_not_called()
    db.rollback.assert_called_once()


def test_missing_action_cannot_execute():
    db = setup_db(None)

    with patch(
        "app.services.action_executor.create_ticket"
    ) as mock_create:
        with pytest.raises(LookupError, match="not found"):
            execute_action(db=db, action_id=999)

    mock_create.assert_not_called()
    db.rollback.assert_called_once()


def test_approved_action_creates_ticket_and_marks_executed():
    action = make_action("approved")
    db = setup_db(action)
    expected_ticket = {"id": 42, "title": "Test ticket"}

    with patch(
        "app.services.action_executor.create_ticket",
        return_value=expected_ticket,
    ) as mock_create:
        result = execute_action(db=db, action_id=1)

    assert action.status == "executed"
    assert result == {
        "action_id": 1,
        "action_status": "executed",
        "ticket": expected_ticket,
    }

    mock_create.assert_called_once_with(
        db=db,
        customer_id=1,
        title="Test ticket",
        description="Testing action execution",
    )
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(action)

def test_ticket_creation_failure_rolls_back_transaction(monkeypatch):
    db = SessionLocal()
    action = None

    try:
        from app.models.customer import Customer

        customer = db.get(Customer, 1)
        assert customer is not None, "Test customer ID 1 must exist."

        tickets_before = db.scalar(
            select(func.count()).select_from(Ticket)
        )

        # Create a real approved action in PostgreSQL.
        action = Action(
            action_type="create_ticket",
            customer_id=customer.id,
            title="Rollback test ticket",
            description="This ticket must not persist.",
            reason="Testing transaction rollback.",
            status="approved",
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        action_id = action.id

        # Use the real ticket creator, then simulate a failure.
        from app.services.tools.write_tools import create_ticket as real_create_ticket

        def create_ticket_then_fail(**kwargs):
            real_create_ticket(**kwargs)
            raise RuntimeError("Simulated failure after ticket flush.")

        monkeypatch.setattr(
            "app.services.action_executor.create_ticket",
            create_ticket_then_fail,
        )

        with pytest.raises(RuntimeError, match="Simulated failure"):
            execute_action(db=db, action_id=action_id)

        # Confirm the action remains approved.
        db.refresh(action)
        assert action.status == "approved"

        # Confirm the uncommitted ticket was rolled back.
        tickets_after = db.scalar(
            select(func.count()).select_from(Ticket)
        )
        assert tickets_after == tickets_before

    finally:
        db.rollback()

        if action is not None:
            db.delete(action)
            db.commit()

        db.close()

def test_concurrent_execution_creates_only_one_ticket(monkeypatch):
    title = f"Concurrent execution test {uuid4()}"

    setup_db = SessionLocal()
    action_id = None

    try:
        # Confirm the customer used by this test exists.
        from app.models.customer import Customer

        customer = setup_db.get(Customer, 1)
        assert customer is not None, "Test customer ID 1 must exist."

        # Create an approved action in the real PostgreSQL database.
        action = Action(
            action_type="create_ticket",
            customer_id=customer.id,
            title=title,
            description="Testing concurrent execution.",
            reason="Verify duplicate ticket prevention.",
            status="approved",
        )
        setup_db.add(action)
        setup_db.commit()
        setup_db.refresh(action)
        action_id = action.id

    finally:
        setup_db.close()

    # Coordinate the two execution attempts.
    ticket_flushed = Event()
    allow_first_to_finish = Event()

    from app.services.tools.write_tools import (
        create_ticket as real_create_ticket,
    )

    def create_ticket_and_pause(**kwargs):
        # Create the ticket inside the first request's transaction.
        result = real_create_ticket(**kwargs)

        # Signal that the first request has created its uncommitted ticket.
        ticket_flushed.set()

        # Keep its transaction open while the second request starts.
        if not allow_first_to_finish.wait(timeout=10):
            raise RuntimeError("Timed out waiting to finish execution.")

        return result

    monkeypatch.setattr(
        "app.services.action_executor.create_ticket",
        create_ticket_and_pause,
    )

    def run_execution():
        # Each concurrent request must use its own database session.
        db = SessionLocal()
        try:
            return execute_action(db=db, action_id=action_id)
        finally:
            db.close()

    second_started = Event()

    def run_second_execution():
        second_started.set()
        return run_execution()

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run_execution)

            # The first request holds the action lock and has flushed its ticket.
            assert ticket_flushed.wait(timeout=10), (
                "The first execution did not reach ticket creation."
            )

            second = pool.submit(run_second_execution)

            assert second_started.wait(timeout=10), (
                "The second execution did not start."
            )

            # Let the first request commit. The second must then see
            # the action's executed status and refuse to create another ticket.
            allow_first_to_finish.set()

            first_result = first.result(timeout=15)

            with pytest.raises(ValueError, match="must be approved"):
                second.result(timeout=15)

        assert first_result["action_status"] == "executed"

        # Verify the final state directly in PostgreSQL.
        check_db = SessionLocal()
        try:
            action_status = check_db.scalar(
                select(Action.status).where(Action.id == action_id)
            )

            ticket_count = check_db.scalar(
                select(func.count())
                .select_from(Ticket)
                .where(Ticket.title == title)
            )

            assert action_status == "executed"
            assert ticket_count == 1

        finally:
            check_db.close()

    finally:
        # Always release the first worker, even if an assertion fails.
        allow_first_to_finish.set()

        # Remove the test data so repeated test runs stay clean.
        cleanup_db = SessionLocal()
        try:
            cleanup_db.execute(
                delete(Ticket).where(Ticket.title == title)
            )

            if action_id is not None:
                cleanup_db.execute(
                    delete(Action).where(Action.id == action_id)
                )

            cleanup_db.commit()

        except Exception:
            cleanup_db.rollback()
            raise

        finally:
            cleanup_db.close()

