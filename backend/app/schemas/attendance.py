from datetime import date
from typing import List

from pydantic import BaseModel


# ---------- For GET /attendance/ (overlay load) ----------

class AttendanceRowOut(BaseModel):
    """
    One row returned to the front-end when loading attendance
    for a specific date.

    This matches what the JS expects:
    - employee_id
    - emp_code
    - name
    - attendance_date
    - status
    """
    employee_id: int
    emp_code: str
    name: str
    attendance_date: date
    status: str


# ---------- For POST /attendance/ (save) ----------

class AttendanceItem(BaseModel):
    """
    One attendance record to be saved/updated.
    This matches what the JS sends in saveAttendance():
    {
      employee_id,
      attendance_date,
      status
    }
    """
    employee_id: int
    attendance_date: date
    status: str


class AttendanceSaveRequest(BaseModel):
    """
    Wrapper object for bulk save:
    {
      "items": [ ... AttendanceItem ... ]
    }
    """
    items: List[AttendanceItem]


# ---------- For GET /attendance/summary (month view) ----------

class DaySummary(BaseModel):
    """
    Summary for a single date in a month:
    - date: 2025-12-01
    - marked: true if at least one attendance row exists in DB
    """
    date: date
    marked: bool


class MonthSummary(BaseModel):
    """
    Summary for entire month used in the overview table.
    Example:
    {
      "month": "2025-12",
      "days": [
        { "date": "2025-12-01", "marked": true },
        { "date": "2025-12-02", "marked": false },
        ...
      ]
    }
    """
    month: str
    days: List[DaySummary]
