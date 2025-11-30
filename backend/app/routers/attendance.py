from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..schemas.attendance import (
    AttendanceEmployeeRow,
    AttendanceUpdateRequest,
)
from ..utils.status_refresh import refresh_employee_statuses

router = APIRouter(prefix="/attendance", tags=["attendance"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[AttendanceEmployeeRow])
def get_attendance(
    today: date,
    attendance_date: date,
    db: Session = Depends(get_db),
):
    # Business rule: attendance_date must equal today
    if attendance_date != today:
        raise HTTPException(
            status_code=400,
            detail="Attendance date must be equal to today.",
        )

    # 1) Refresh employee statuses for this 'today'
    refresh_employee_statuses(today=today, db=db)

    # 2) Get employees who are currently Active
    #    (Inactive / Offboarded / Vacation are filtered out)
    active_employees = (
        db.query(Employee)
        .filter(Employee.current_status == "Active")
        .all()
    )

    rows: List[AttendanceEmployeeRow] = []

    for emp in active_employees:
        # Check existing attendance for this employee + date
        att = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == emp.id,
                Attendance.attendance_date == attendance_date,
            )
            .first()
        )

        if att:
            status = att.status
        else:
            # Default = Present
            status = "Present"

        rows.append(
            AttendanceEmployeeRow(
                employee_id=emp.id,
                emp_code=emp.emp_code,
                name=emp.name,
                attendance_date=attendance_date,
                status=status,
            )
        )

    return rows


@router.post("/")
def save_attendance(
    payload: AttendanceUpdateRequest,
    db: Session = Depends(get_db),
):
    # Upsert attendance rows
    for item in payload.items:
        att = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == item.employee_id,
                Attendance.attendance_date == item.attendance_date,
            )
            .first()
        )

        if att:
            att.status = item.status
        else:
            att = Attendance(
                employee_id=item.employee_id,
                attendance_date=item.attendance_date,
                status=item.status,
            )
            db.add(att)

    db.commit()
    return {"updated": len(payload.items)}
