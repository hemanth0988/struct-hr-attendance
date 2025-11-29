from pydantic import BaseModel
from datetime import date
from typing import Optional


class EmployeeBase(BaseModel):
    name: str
    joining_date: date

    basic_pay_monthly: float
    transport_monthly: float
    accommodation_monthly: float
    other_monthly: float

    paid_leave_daily: float
    vacation_pay_daily: float


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    current_status: Optional[str] = None
    status_change_date: Optional[date] = None
    upcoming_status: Optional[str] = None


class EmployeeOut(EmployeeBase):
    id: int
    emp_code: str
    current_status: str
    status_change_date: Optional[date]
    upcoming_status: Optional[Optional[str]]
    total_salary_monthly: float

    class Config:
        orm_mode = True
