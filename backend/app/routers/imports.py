"""Validated CSV bulk imports for workspace customer and ticket records."""
import csv
import io
import re
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import require_role
from app.db.database import get_db
from app.models.customer import Customer
from app.models.ticket import Ticket
from app.models.user import User
from app.services.audit import record_event

router = APIRouter(prefix="/api/v1/imports", tags=["bulk imports"])
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 5000


class ImportErrorRow(BaseModel):
    row: int
    message: str


class ImportPreview(BaseModel):
    kind: Literal["customers", "tickets"]
    total_rows: int
    ready_to_import: int
    skipped_duplicates: int = 0
    errors: list[ImportErrorRow]
    preview: list[dict]
    imported: int | None = None


def _read_csv(content: bytes, expected_headers: set[str]) -> list[tuple[int, dict[str, str]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="Upload a UTF-8 encoded CSV file.") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    normalized_headers = [(header or "").strip().lower() for header in (reader.fieldnames or [])]
    if not normalized_headers or len(set(normalized_headers)) != len(normalized_headers):
        raise HTTPException(status_code=422, detail="CSV must have a single, non-empty header for each column.")
    headers = set(normalized_headers)
    missing = expected_headers - headers
    if missing:
        raise HTTPException(status_code=422, detail={"message": "Required CSV columns are missing.", "missing_columns": sorted(missing)})
    rows = []
    for line, raw in enumerate(reader, start=2):
        if line > MAX_ROWS + 1:
            raise HTTPException(status_code=413, detail=f"A single import may contain at most {MAX_ROWS} rows.")
        if None in raw:
            raise HTTPException(status_code=422, detail=f"CSV row {line} has more values than the header columns.")
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in raw.items()}
        if not any(row.values()):
            continue
        rows.append((line, row))
    return rows


@router.post("/{kind}", response_model=ImportPreview)
async def import_csv(
    kind: Literal["customers", "tickets"],
    file: UploadFile = File(...),
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
    actor: User = Depends(require_role("admin", "agent")),
):
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="CSV files must be 10 MB or smaller.")
    if kind == "customers":
        rows = _read_csv(content, {"name", "email"})
        existing = {email.lower() for email in db.execute(select(Customer.email)).scalars().all()}
        seen: set[str] = set()
        ready: list[dict] = []
        errors: list[ImportErrorRow] = []
        skipped = 0
        for line, row in rows:
            name, email, company = row.get("name", ""), row.get("email", "").lower(), row.get("company", "")
            if len(name) < 2 or len(name) > 255:
                errors.append(ImportErrorRow(row=line, message="Name must contain 2 to 255 characters."))
            elif len(email) > 255 or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is None:
                errors.append(ImportErrorRow(row=line, message="Enter a valid email address."))
            elif len(company) > 255:
                errors.append(ImportErrorRow(row=line, message="Company must be 255 characters or fewer."))
            elif email in existing or email in seen:
                skipped += 1
            else:
                seen.add(email)
                ready.append({"name": name, "email": email, "company": company or None})
        if errors:
            return ImportPreview(kind=kind, total_rows=len(rows), ready_to_import=len(ready), skipped_duplicates=skipped, errors=errors, preview=ready[:10])
        if not dry_run:
            try:
                db.add_all(Customer(**row) for row in ready)
                db.flush()
                if ready:
                    record_event(db, actor, "customer.bulk_imported", "customer", None, {"count": len(ready), "skipped_duplicates": skipped})
                else:
                    db.rollback()
            except IntegrityError as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail="The import conflicted with a customer added at the same time. Preview the file again.") from exc
        return ImportPreview(kind=kind, total_rows=len(rows), ready_to_import=len(ready), skipped_duplicates=skipped, errors=[], preview=ready[:10], imported=None if dry_run else len(ready))

    rows = _read_csv(content, {"external_id", "customer_email", "title", "description"})
    customers = {email.lower(): customer for customer in db.execute(select(Customer)).scalars().all() for email in [customer.email]}
    existing_external_ids = set(db.execute(select(Ticket.external_id).where(Ticket.external_id.is_not(None))).scalars().all())
    seen_external_ids: set[str] = set()
    ready_tickets: list[dict] = []
    errors = []
    skipped = 0
    priorities = {"low", "medium", "high", "urgent"}
    statuses = {"open", "in_progress", "resolved", "closed"}
    for line, row in rows:
        email = row.get("customer_email", "").lower()
        customer = customers.get(email)
        external_id = row.get("external_id", "")
        priority = (row.get("priority") or "medium").lower()
        status = (row.get("status") or "open").lower()
        messages = []
        if customer is None:
            messages.append("Customer email does not match an existing customer.")
        if not row.get("title") or len(row["title"]) > 255:
            messages.append("Title is required and must be 255 characters or fewer.")
        if not row.get("description"):
            messages.append("Description is required.")
        if not external_id or len(external_id) > 128:
            messages.append("A stable source ticket ID is required (maximum 128 characters).")
        if priority not in priorities:
            messages.append("Priority must be low, medium, high, or urgent.")
        if status not in statuses:
            messages.append("Status must be open, in_progress, resolved, or closed.")
        if messages:
            errors.append(ImportErrorRow(row=line, message=" ".join(messages)))
        elif external_id in existing_external_ids or external_id in seen_external_ids:
            skipped += 1
        else:
            seen_external_ids.add(external_id)
            ready_tickets.append({"external_id": external_id, "customer_id": customer.id, "title": row["title"], "description": row["description"], "priority": priority, "status": status})
    if errors:
        return ImportPreview(kind=kind, total_rows=len(rows), ready_to_import=len(ready_tickets), skipped_duplicates=skipped, errors=errors, preview=ready_tickets[:10])
    if not dry_run:
        try:
            db.add_all(Ticket(**row) for row in ready_tickets)
            db.flush()
            if ready_tickets:
                record_event(db, actor, "ticket.bulk_imported", "ticket", None, {"count": len(ready_tickets), "skipped_duplicates": skipped})
            else:
                db.rollback()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="The import conflicted with another ticket import. Preview the file again.") from exc
    return ImportPreview(kind=kind, total_rows=len(rows), ready_to_import=len(ready_tickets), skipped_duplicates=skipped, errors=[], preview=ready_tickets[:10], imported=None if dry_run else len(ready_tickets))
