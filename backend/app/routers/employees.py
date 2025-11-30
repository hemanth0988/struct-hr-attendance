from datetime import date
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.employee import Employee

router = APIRouter(prefix="/employees", tags=["employees"])


# ---------- Pydantic Schemas ----------

class EmployeeCreate(BaseModel):
    name: str
    joining_date: date
    basic_pay_monthly: float
    transport_monthly: float
    accommodation_monthly: float
    other_monthly: float
    paid_leave_daily: float
    vacation_pay_daily: float


class EmployeeResponse(BaseModel):
    id: int
    emp_code: str
    name: str
    joining_date: date
    current_status: str
    status_change_date: Optional[date] = None
    upcoming_status: Optional[str] = None

    class Config:
        orm_mode = True


class EmployeeStatusUpdate(BaseModel):
    """
    Used by the Employee Status page to set an upcoming status
    and a date when that status should become active.
    """
    upcoming_status: Optional[Literal["Active", "Vacation", "Offboarded"]] = None
    status_change_date: Optional[date] = None


# ---------- Dependency ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Helpers ----------

def generate_emp_code(db: Session) -> str:
    """
    Simple EMP01, EMP02, ... generator based on current count.
    """
    last = db.query(Employee).order_by(Employee.id.desc()).first()
    if not last or not last.emp_code or not last.emp_code.startswith("EMP"):
        return "EMP01"
    try:
        num = int(last.emp_code.replace("EMP", ""))
    except ValueError:
        num = 0
    return f"EMP{num + 1:02d}"


# ---------- Routes ----------

@router.get("/", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    """
    Return all employees, including current_status, status_change_date and upcoming_status.
    This is used by:
      - Add Employee page (bottom table)
      - Employee Status page
    """
    employees = db.query(Employee).order_by(Employee.id.asc()).all()
    return employees


@router.post("/", response_model=EmployeeResponse)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    """
    Create a new employee.
    current_status is:
      - 'Inactive' if joining_date is in the future
      - 'Active' otherwise
    """
    emp_code = generate_emp_code(db)

    today = date.today()
    if payload.joining_date > today:
        current_status = "Inactive"
    else:
        current_status = "Active"

    emp = Employee(
        emp_code=emp_code,
        name=payload.name,
        joining_date=payload.joining_date,
        current_status=current_status,
        basic_pay_monthly=payload.basic_pay_monthly,
        transport_monthly=payload.transport_monthly,
        accommodation_monthly=payload.accommodation_monthly,
        other_monthly=payload.other_monthly,
        paid_leave_daily=payload.paid_leave_daily,
        vacation_pay_daily=payload.vacation_pay_daily,
        status_change_date=None,
        upcoming_status=None,
    )

    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.patch("/{employee_id}/status", response_model=EmployeeResponse)
def update_employee_status(
    employee_id: int,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Set an upcoming status + the date from which it should apply.
    - User NEVER changes current_status directly.
    - When attendance uses a "today" date that reaches status_change_date,
      another piece of logic (in attendance router) will:
          upcoming_status -> current_status
          clear upcoming_status + status_change_date
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # If both are None, this effectively clears any future change
    emp.upcoming_status = payload.upcoming_status
    emp.status_change_date = payload.status_change_date

    db.commit()
    db.refresh(emp)
    return emp
