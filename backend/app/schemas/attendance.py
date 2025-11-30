from datetime import date
from typing import List
from pydantic import BaseModel


# For sending each employee's row to the frontend
class AttendanceEmployeeRow(BaseModel):
    employee_id: int
    emp_code: str
    name: str
    attendance_date: date
    status: str  # Present / PaidLeave / UnpaidLeave


# For saving attendance back from frontend
class AttendanceUpdateItem(BaseModel):
    employee_id: int
    attendance_date: date
    status: str  # Present / PaidLeave / UnpaidLeave


class AttendanceUpdateRequest(BaseModel):
    items: List[AttendanceUpdateItem]
