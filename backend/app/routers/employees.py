from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.employee import Employee
from ..schemas.employee import EmployeeCreate, EmployeeStatusUpdate
from ..utils.status_refresh import refresh_employee_statuses


router = APIRouter(
    prefix="/employees",
    tags=["employees"],
)


# ---------------------------------------
# Helper: generate next EMP code (EMP01…)
# ---------------------------------------
def _generate_emp_code(db: Session) -> str:
    last = db.query(Employee).order_by(Employee.id.desc()).first()
    next_number = 1 if last is None else (last.id + 1)
    return f"EMP{next_number:02d}"


# ---------------------------------------
# GET /employees/  → list all employees
# Optional: today=YYYY-MM-DD to apply status refresh
# ---------------------------------------
@router.get("/")
def list_employees(
    today: date | None = None,
    db: Session = Depends(get_db),
):
    # If a manual Today is supplied, refresh statuses first
    if today is not None:
        refresh_employee_statuses(today=today, db=db)

    employees = db.query(Employee).order_by(Employee.id.asc()).all()
    return employees


# ---------------------------------------
# POST /employees/  → create employee
# Optional query param: today=YYYY-MM-DD (manual Today from UI)
# ---------------------------------------
@router.post("/")
def create_employee(
    payload: EmployeeCreate,
    today: date | None = None,
    db: Session = Depends(get_db),
):
    # Decide current_status from joining date using manual Today if given
    today_ref = today or date.today()
    if payload.joining_date > today_ref:
        current_status = "Inactive"
    else:
        current_status = "Active"

    # Salary numbers from payload
    basic_monthly = payload.basic_pay_monthly
    transport_monthly = payload.transport_monthly
    accommodation_monthly = payload.accommodation_monthly
    other_monthly = payload.other_monthly

    total_salary_monthly = (
        basic_monthly
        + transport_monthly
        + accommodation_monthly
        + other_monthly
    )

    emp = Employee(
        emp_code=_generate_emp_code(db),
        name=payload.name,
        joining_date=payload.joining_date,
        current_status=current_status,
        upcoming_status=None,
        status_change_date=None,
        basic_pay_monthly=basic_monthly,
        transport_monthly=transport_monthly,
        accommodation_monthly=accommodation_monthly,
        other_monthly=other_monthly,
        paid_leave_daily=payload.paid_leave_daily,
        vacation_pay_daily=payload.vacation_pay_daily,
        total_salary_monthly=total_salary_monthly,
    )

    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


# ---------------------------------------
# PATCH /employees/{emp_code}/status  → update a single employee's upcoming status
# (still there if you ever want to use it individually)
# ---------------------------------------
@router.patch("/{emp_code}/status")
def update_employee_status(
    emp_code: str,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
):
    emp = (
        db.query(Employee)
        .filter(Employee.emp_code == emp_code)
        .first()
    )

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.upcoming_status = payload.upcoming_status
    emp.status_change_date = payload.status_change_date

    db.commit()
    db.refresh(emp)
    return emp


# ---------------------------------------
# Bulk status changes – matches frontend "changes" payload
# POST /employees/status-changes
# ---------------------------------------
class StatusChangeItem(BaseModel):
    emp_code: str
    new_status: str
    effective_date: date


class StatusChangeRequest(BaseModel):
    today: date
    changes: List[StatusChangeItem]


@router.post("/status-changes")
def apply_status_changes(
    req: StatusChangeRequest,
    db: Session = Depends(get_db),
):
    # Basic validation: effective dates should not be earlier than 'today'
    for item in req.changes:
        if item.effective_date < req.today:
            raise HTTPException(
                status_code=400,
                detail=f"Effective date for {item.emp_code} cannot be earlier than Today.",
            )

    updated = 0
    for item in req.changes:
        emp = (
            db.query(Employee)
            .filter(Employee.emp_code == item.emp_code)
            .first()
        )
        if not emp:
            # Skip missing employees; could also raise instead
            continue

        emp.upcoming_status = item.new_status
        emp.status_change_date = item.effective_date
        updated += 1

    db.commit()

    # After scheduling changes, we can optionally refresh immediately
    # in case some effective_date == today
    refresh_employee_statuses(today=req.today, db=db)

    return {"updated": updated}
