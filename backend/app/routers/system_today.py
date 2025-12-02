from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.system_today import SystemToday
from ..schemas.system_today import SystemTodayOut, SystemTodayUpdate

router = APIRouter(
    prefix="/system",
    tags=["system"],
)


def _get_singleton_row(db: Session) -> SystemToday:
    """
    Get the single SystemToday row (id = 1).
    Create it if it does not exist yet.
    """
    row: Optional[SystemToday] = db.query(SystemToday).filter(SystemToday.id == 1).first()
    if not row:
        row = SystemToday(id=1, manual_today=None)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/today", response_model=SystemTodayOut)
def get_system_today(
    db: Session = Depends(get_db),
):
    """
    Return the globally locked 'Today' date from the database.

    Example:
    { "today": "2025-12-02" }
    or
    { "today": null } if not set yet.
    """
    row = _get_singleton_row(db)
    return SystemTodayOut(today=row.manual_today)


@router.post("/today", response_model=SystemTodayOut)
def set_system_today(
    payload: SystemTodayUpdate,
    db: Session = Depends(get_db),
):
    """
    Update the globally locked 'Today' date.

    Rules:
    - If manual_today is currently NULL -> accept any date.
    - If manual_today is set and new 'today' < existing -> reject.
    - Otherwise, update it to the new date.

    This ensures that 'Today' can never move backwards globally.
    """
    new_today: date = payload.today
    row = _get_singleton_row(db)

    if row.manual_today is not None and new_today < row.manual_today:
        # Reject going backwards
        raise HTTPException(
            status_code=400,
            detail=f"Today cannot be earlier than existing system date {row.manual_today.isoformat()}",
        )

    row.manual_today = new_today
    db.add(row)
    db.commit()
    db.refresh(row)

    return SystemTodayOut(today=row.manual_today)
