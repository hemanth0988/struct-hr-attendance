from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.employee import Employee
from ..schemas.employee import EmployeeCreate, EmployeeStatusUpdate

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
# ---------------------------------------
@router.get("/")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees


# ---------------------------------------
# POST /employees/  → create employee
# ---------------------------------------
@router.post("/")
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    # Decide current_status from joining date
    today = date.today()
    if payload.joining_date > today:
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


# -----------------------------------------------------
# PATCH /employees/{emp_code}/status  → upcoming status
# -----------------------------------------------------
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
