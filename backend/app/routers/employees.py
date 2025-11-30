from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.employee import Employee
from ..models.attendance import Attendance
from ..schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

router = APIRouter(prefix="/employees", tags=["employees"])


# -------------------------------------------------------------------
# DB dependency
# -------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def generate_emp_code(db: Session) -> str:
    """
    Generate next EMP code as EMP01, EMP02, ...
    based on the last employee in the table.
    """
    last_emp = db.query(Employee).order_by(Employee.id.desc()).first()
    if last_emp and last_emp.emp_code and last_emp.emp_code.startswith("EMP"):
        try:
            last_num = int(last_emp.emp_code[3:])
        except ValueError:
            last_num = 0
    else:
        last_num = 0

    return f"EMP{last_num + 1:02d}"


def determine_initial_status(joining_date: date) -> str:
    """
    For a brand-new employee:
    - If joining_date > real today  → Inactive
    - Else                         → Active
    """
    today_real = date.today()
    return "Inactive" if joining_date > today_real else "Active"


# -------------------------------------------------------------------
# List employees
# -------------------------------------------------------------------
@router.get("/", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.id.asc()).all()
    return employees


# -------------------------------------------------------------------
# Create employee
# -------------------------------------------------------------------
@router.post("/", response_model=EmployeeResponse)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Create a new employee.

    - Auto-generates EMP code (EMP01, EMP02, …)
    - Sets initial current_status from joining_date
    - Computes total_salary_monthly (cannot be NULL in DB)
    """

    emp_code = generate_emp_code(db)
    current_status = determine_initial_status(payload.joining_date)

    # Total monthly salary must never be NULL
    total_salary_monthly = (
        (payload.basic_pay_monthly or 0)
        + (payload.transport_monthly or 0)
        + (payload.accommodation_monthly or 0)
        + (payload.other_monthly or 0)
    )

    employee = Employee(
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
        total_salary_monthly=total_salary_monthly,
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


# -------------------------------------------------------------------
# Update upcoming status for an employee
# -------------------------------------------------------------------
@router.patch("/{employee_id}/status", response_model=EmployeeResponse)
def update_employee_status(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
):
    """
    Only upcoming_status + status_change_date are user-editable.
    current_status is always controlled by the system.
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.upcoming_status = payload.upcoming_status
    emp.status_change_date = payload.status_change_date

    db.commit()
    db.refresh(emp)
    return emp


# -------------------------------------------------------------------
# Reset all data (employees + attendance) – for testing only
# -------------------------------------------------------------------
@router.post("/reset-all", response_model=dict)
def reset_all_data(db: Session = Depends(get_db)):
    """
    Danger zone: wipe all employees and attendance.

    This is only for your test environment, so we don't
    do any authentication on purpose (as you requested).
    """

    db.query(Attendance).delete()
    db.query(Employee).delete()
    db.commit()

    return {"message": "All employees and attendance records have been deleted."}
