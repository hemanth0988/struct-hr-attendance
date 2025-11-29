from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.employee import Employee
from ..schemas.employee import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeStatusUpdate,
)

router = APIRouter(prefix="/employees", tags=["employees"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=EmployeeOut)
def create_employee(employee_in: EmployeeCreate, db: Session = Depends(get_db)):
    # Calculate total salary monthly
    total_salary_monthly = (
        employee_in.basic_pay_monthly
        + employee_in.transport_monthly
        + employee_in.accommodation_monthly
        + employee_in.other_monthly
    )

    db_employee = Employee(
        name=employee_in.name,
        joining_date=employee_in.joining_date,
        basic_pay_monthly=employee_in.basic_pay_monthly,
        transport_monthly=employee_in.transport_monthly,
        accommodation_monthly=employee_in.accommodation_monthly,
        other_monthly=employee_in.other_monthly,
        total_salary_monthly=total_salary_monthly,
        paid_leave_daily=employee_in.paid_leave_daily,
        vacation_pay_daily=employee_in.vacation_pay_daily,
        current_status="Active",  # default on create
    )

    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    # Generate emp_code like EMP01, EMP02...
    if not db_employee.emp_code:
        db_employee.emp_code = f"EMP{db_employee.id:02d}"
        db.commit()
        db.refresh(db_employee)

    return db_employee


@router.get("/", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees


@router.patch("/{employee_id}/status", response_model=EmployeeOut)
def update_employee_status(
    employee_id: int,
    payload: EmployeeStatusUpdate,
    db: Session = Depends(get_db),
):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    emp.status_change_date = payload.status_change_date
    emp.upcoming_status = payload.upcoming_status

    db.commit()
    db.refresh(emp)
    return emp
