from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..schemas.attendance import (
    AttendanceRowOut,
    AttendanceSaveRequest,
    MonthSummary,
    DaySummary,
)
from ..utils.status_refresh import refresh_employee_statuses

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"],
)


# ---------------------------------------------------------
# GET /attendance/  -> load attendance rows for a given day
# ---------------------------------------------------------
@router.get("/", response_model=List[AttendanceRowOut])
def get_attendance_for_day(
    today: date = Query(..., description="Manual 'today' date for status logic"),
    attendance_date: date = Query(..., description="Date to load attendance for"),
    db: Session = Depends(get_db),
):
    """
    Load attendance rows for a given date.

    Steps:
    1. Refresh employee statuses using 'today'.
    2. Find all employees who are Active on 'today'.
    3. For each such employee, see if an Attendance row exists for attendance_date.
       - If exists -> use its status.
       - If not   -> default status = 'Present'.
    """
    # 1) Refresh statuses so Employee.current_status is correct
    refresh_employee_statuses(today, db)

    # 2) Active employees as of 'today'
    active_emps: List[Employee] = (
        db.query(Employee)
        .filter(Employee.current_status == "Active")
        .order_by(Employee.emp_code.asc())
        .all()
    )

    if not active_emps:
        return []

    # 3) Get any already-stored attendance rows for this date
    emp_ids = [e.id for e in active_emps]
    existing_rows: List[Attendance] = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id.in_(emp_ids),
            Attendance.attendance_date == attendance_date,
        )
        .all()
    )
    by_emp_id = {row.employee_id: row for row in existing_rows}

    result: List[AttendanceRowOut] = []
    for emp in active_emps:
        existing = by_emp_id.get(emp.id)
        if existing:
            status = existing.status
        else:
            # default if nothing saved yet
            status = "Present"

        result.append(
            AttendanceRowOut(
                employee_id=emp.id,
                emp_code=emp.emp_code,
                name=emp.name,
                attendance_date=attendance_date,
                status=status,
            )
        )

    return result


# ---------------------------------------------------------
# POST /attendance/  -> save/update attendance in bulk
# ---------------------------------------------------------
@router.post("/")
def save_attendance(
    payload: AttendanceSaveRequest,
    db: Session = Depends(get_db),
):
    """
    Save attendance rows in bulk.

    For each item:
    - If a row (employee_id, attendance_date) exists -> update status
    - Else -> insert a new row
    """
    if not payload.items:
        raise HTTPException(status_code=400, detail="No attendance items provided")

    updated_count = 0

    for item in payload.items:
        # Ensure date is a proper date object (Pydantic usually does this)
        att_date = item.attendance_date

        row: Attendance = (
            db.query(Attendance)
            .filter(
                Attendance.employee_id == item.employee_id,
                Attendance.attendance_date == att_date,
            )
            .first()
        )

        if row:
            row.status = item.status
        else:
            row = Attendance(
                employee_id=item.employee_id,
                attendance_date=att_date,
                status=item.status,
            )
            db.add(row)

        updated_count += 1

    db.commit()

    return {"updated": updated_count}


# -----------------------------------------------------------------
# GET /attendance/summary  -> which dates in the month are "marked"
# -----------------------------------------------------------------
@router.get("/summary", response_model=MonthSummary)
def get_month_summary(
    today: date = Query(..., description="Manual 'today' used to pick month"),
    db: Session = Depends(get_db),
):
    """
    Return which dates in the month of 'today' have ANY attendance records.

    Response shape:
    {
      "month": "2025-12",
      "days": [
        { "date": "2025-12-01", "marked": true },
        { "date": "2025-12-02", "marked": false },
        ...
      ]
    }
    """
    year = today.year
    month = today.month

    # First day of this month
    first_day = date(year, month, 1)
    # First day of next month
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)

    # All distinct dates that have at least one attendance row
    rows = (
        db.query(Attendance.attendance_date)
        .filter(
            Attendance.attendance_date >= first_day,
            Attendance.attendance_date < next_month_first,
        )
        .group_by(Attendance.attendance_date)
        .all()
    )

    marked_dates = {r[0] for r in rows}  # set of date objects

    # Build full list for every day in month
    days: List[DaySummary] = []
    current = first_day
    while current < next_month_first:
        days.append(
            DaySummary(
                date=current,
                marked=current in marked_dates,
            )
        )
        current = date.fromordinal(current.toordinal() + 1)

    month_str = f"{year:04d}-{month:02d}"
    return MonthSummary(month=month_str, days=days)
