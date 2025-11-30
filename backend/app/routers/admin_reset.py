from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import SessionLocal

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/reset")
def reset_database(db: Session = Depends(get_db)):
    """
    Wipe ALL data from employees + attendance tables.
    NO password, just a confirm on the frontend.
    """
    try:
        # Disable FK checks, truncate both tables, re-enable
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.execute(text("TRUNCATE TABLE attendance;"))
        db.execute(text("TRUNCATE TABLE employees;"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")

    return {"message": "Database reset successfully."}
