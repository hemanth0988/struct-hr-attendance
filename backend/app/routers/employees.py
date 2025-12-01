from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.employee import Employee
from ..schemas.employee import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeStatusUpdate,
    EmployeeStatusChangeItem,
    EmployeeStatusChangeRequest,
    EmployeeSalaryUpdate,
)
from ..utils.status_refresh import refresh_employee_statuses

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
)


# ---------- Helpers ----------

def _generate_emp_code(db: Session) -> str:
    """
    Generate the next employee code like EMP01, EMP02, ...
    """
    last = db.query(Employee).order_by(Employee.id.desc()).first()
    if not last or not last.emp_code or not last.emp_code.startswith("EMP"):
        # Fallback if no employees yet or weird code
        next_num = 1
    else:
        try:
            num_part = int(last.emp_code.replace("EMP", ""))
        except ValueError:
            num_part = last.id or 0
        next_num = num_part + 1

    return f"EMP{next_num:02d}"


def _calc_total_monthly(payload) -> float:
    return (
        float(payload.basic_pay_monthly)
        + float(payload.transport_monthly)
        + float(payload.accommodation_monthly)
        + float(payload.other_monthly)
    )


# ---------- Routes ----------

@router.get("/", response_model=List[EmployeeOut])
def list_employees(
    today: date = Query(..., description="Manual 'today' date used for status logic"),
    db: Session = Depends(get_db),
):
    """
    List employees for a given 'today' date.
    Before returning, we refresh statuses using that date.
    """
    refresh_employee_statuses(today, db)

    employees = (
        db.query(Employee)
        .order_by(Employee.emp_code.asc())
        .all()
    )
    return employees


@router.post("/", response_model=EmployeeOut)
def create_employee(
    payload: EmployeeCreate,
    today: date = Query(..., description="Manual 'today' date used for initial status"),
    db: Session = Depends(get_db),
):
    """
    Create a new employee. Initial status is based on joining_date vs today:

    - joining_date <= today  -> current_status = 'Active'
    - joining_date > today   -> current_status = 'Inactive'
    """
    emp_code = _generate_emp_code(db)
    total_monthly = _calc_total_monthly(payload)

    # Decide initial status
    if payload.joining_date > today:
        current_status = "Inactive"
    else:
        current_status = "Active"

    emp = Employee(
        emp_code=emp_code,
        name=payload.name,
        joining_date=payload.joining_date,
        current_status=current_status,
        status_change_date=None,
        upcoming_status=None,
        basic_pay_monthly=payload.basic_pay_monthly,
        transport_monthly=payload.transport_monthly,
        accommodation_monthly=payload.accommodation_monthly,
        other_monthly=payload.other_monthly,
        paid_leave_daily=payload.paid_leave_daily,
        vacation_pay_daily=payload.vacation_pay_daily,
        total_salary_monthly=total_monthly,
    )

    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.patch("/{emp_code}/status", response_model=EmployeeOut)
def update_employee_status(
    emp_code: str,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Update just the scheduled status for a single employee.
    (Kept for completeness; UI is using the bulk /status-changes.)
    """
    emp = (
        db.query(Employee)
        .filter(Employee.emp_code == emp_code)
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    if payload.upcoming_status is not None:
        emp.upcoming_status = payload.upcoming_status
    if payload.status_change_date is not None:
        emp.status_change_date = payload.status_change_date

    db.commit()
    db.refresh(emp)
    return emp


@router.post("/status-changes")
def apply_status_changes(
    payload: EmployeeStatusChangeRequest,
    db: Session = Depends(get_db),
):
    """
    Apply one or more upcoming status changes.

    For each change:
    - Store upcoming_status and status_change_date.
    - If effective_date <= today, we immediately move it into current_status
      and clear the upcoming fields.

    Finally, we call refresh_employee_statuses(today, db) to ensure
    auto transitions (Inactive -> Active when joining date is reached).
    """
    today = payload.today

    for change in payload.changes:
        emp: Employee = (
            db.query(Employee)
            .filter(Employee.emp_code == change.emp_code)
            .first()
        )
        if not emp:
            # Skip silently if employee not found
            continue

        emp.upcoming_status = change.new_status
        emp.status_change_date = change.effective_date

        # If the effective date is today or earlier, apply immediately
        if change.effective_date <= today:
            emp.current_status = change.new_status
            emp.upcoming_status = None
            emp.status_change_date = None

    db.commit()

    # Apply any other automatic transitions
    refresh_employee_statuses(today, db)

    return {"message": "Status changes applied"}


@router.patch("/{emp_code}", response_model=EmployeeOut)
def update_employee_salary(
    emp_code: str,
    payload: EmployeeSalaryUpdate,
    db: Session = Depends(get_db),
):
    """
    Update salary details for an employee.
    This is what the front-end 'View Salary' overlay calls.
    """
    emp: Employee = (
        db.query(Employee)
        .filter(Employee.emp_code == emp_code)
        .first()
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.basic_pay_monthly = payload.basic_pay_monthly
    emp.transport_monthly = payload.transport_monthly
    emp.accommodation_monthly = payload.accommodation_monthly
    emp.other_monthly = payload.other_monthly
    emp.paid_leave_daily = payload.paid_leave_daily
    emp.vacation_pay_daily = payload.vacation_pay_daily

    emp.total_salary_monthly = (
        float(payload.basic_pay_monthly)
        + float(payload.transport_monthly)
        + float(payload.accommodation_monthly)
        + float(payload.other_monthly)
    )

    db.commit()
    db.refresh(emp)
    return emp
