from datetime import date
from typing import Optional, List

from pydantic import BaseModel


# ---------- Core Employee Schemas ----------

class EmployeeBase(BaseModel):
    """
    Shared fields for creating / returning an employee.
    """
    name: str
    joining_date: date

    # Monthly salary components
    basic_pay_monthly: float
    transport_monthly: float
    accommodation_monthly: float
    other_monthly: float

    # Daily amounts
    paid_leave_daily: float
    vacation_pay_daily: float


class EmployeeCreate(EmployeeBase):
    """
    Request body for creating an employee.
    """
    pass


class EmployeeOut(EmployeeBase):
    """
    Full employee object returned by the API.
    """
    id: int
    emp_code: str

    current_status: str
    status_change_date: Optional[date]
    upcoming_status: Optional[str]

    total_salary_monthly: float

    class Config:
        orm_mode = True


# ---------- Status Update Schemas ----------

class EmployeeStatusUpdate(BaseModel):
    """
    For PATCH /employees/{emp_code}/status (single employee).
    """
    status_change_date: Optional[date] = None
    upcoming_status: Optional[str] = None


class EmployeeStatusChangeItem(BaseModel):
    """
    One row inside the bulk status change request.
    """
    emp_code: str
    new_status: str
    effective_date: date


class EmployeeStatusChangeRequest(BaseModel):
    """
    Request body for POST /employees/status-changes.
    """
    today: date
    changes: List[EmployeeStatusChangeItem]


# ---------- Salary Update Schema ----------

class EmployeeSalaryUpdate(BaseModel):
    """
    For PATCH /employees/{emp_code} – update salary fields.
    """
    basic_pay_monthly: float
    transport_monthly: float
    accommodation_monthly: float
    other_monthly: float
    paid_leave_daily: float
    vacation_pay_daily: float
