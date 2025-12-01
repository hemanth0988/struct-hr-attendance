from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..schemas.attendance import (
    AttendanceEmployeeRow,
    AttendanceUpdateRequest,
)
from ..utils.status_refresh import refresh_employee_statuses

router = APIRouter(prefix="/attendance", tags=["attendance"])


# GET /attendance?attendance_date=YYYY-MM-DD&today=YYYY-MM-DD
# Returns one row per Active employee with their attendance status for that date
@router.get("/", response_model=List[AttendanceEmployeeRow])
def get_attendance_rows(
    attendance_date: date,
    today: date,
    db: Session = Depends(get_db),
):
    # 1) Refresh all employee statuses based on manual Today
    refresh_employee_statuses(today=today, db=db)

    # 2) Get all employees, but we will only send Active ones
    employees = db.query(Employee).order_by(Employee.id.asc()).all()
    rows: List[AttendanceEmployeeRow] = []

    for emp in employees:
        # Only Active employees get attendance rows
        if emp.current_status != "Active":
            continue

        # Check if there is already an attendance record for that date
        att = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == emp.id,
                Attendance.attendance_date == attendance_date,
            )
            .first()
        )

        if att:
            status = att.status  # Present / PaidLeave / UnpaidLeave
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


# POST /attendance
# Saves attendance for the given items (employee_id + date + status)
@router.post("/")
def update_attendance(
    payload: AttendanceUpdateRequest,
    db: Session = Depends(get_db),
):
    if not payload.items:
        return {"updated": 0}

    for item in payload.items:
        # Optional: sanity check, status must be one of the three allowed values
        if item.status not in {"Present", "PaidLeave", "UnpaidLeave"}:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{item.status}' for employee_id={item.employee_id}",
            )

        # Try to find an existing attendance for that employee + date
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
