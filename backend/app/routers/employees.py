from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(
    prefix="/employees",
    tags=["employees"]
)


# -------------------------
# GET ALL EMPLOYEES
# -------------------------
@router.get("/")
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(models.Employee).all()
    return employees


# -------------------------
# CREATE NEW EMPLOYEE
# -------------------------
@router.post("/")
def create_employee(emp: schemas.EmployeeCreate, db: Session = Depends(get_db)):

    # Calculate total salary (sum of all 5 components)
    total_salary = (
        emp.basic_salary_monthly +
        emp.transport_allowance_monthly +
        emp.food_allowance_monthly +
        emp.other_allowance_monthly +
        emp.fixed_allowance_monthly
    )

    new_emp = models.Employee(
        emp_code=emp.emp_code,
        name=emp.name,
        joining_date=emp.joining_date,
        current_status="Active",  # Default
        basic_salary_monthly=emp.basic_salary_monthly,
        transport_allowance_monthly=emp.transport_allowance_monthly,
        food_allowance_monthly=emp.food_allowance_monthly,
        other_allowance_monthly=emp.other_allowance_monthly,
        fixed_allowance_monthly=emp.fixed_allowance_monthly,
        total_salary_monthly=total_salary,
        status_change_date=None,
        upcoming_status=None
    )

    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)

    return {"message": "Employee created successfully", "employee": new_emp}


# -------------------------
# UPDATE EMPLOYEE STATUS (UPCOMING STATUS)
# -------------------------
@router.patch("/{emp_code}/status")
def update_employee_status(emp_code: str, data: schemas.EmployeeStatusUpdate, db: Session = Depends(get_db)):

    emp = db.query(models.Employee).filter(models.Employee.emp_code == emp_code).first()

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # User cannot directly modify current status
    emp.upcoming_status = data.upcoming_status
    emp.status_change_date = data.status_change_date

    db.commit()
    db.refresh(emp)

    return {"message": "Status updated", "employee": emp}
