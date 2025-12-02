from datetime import date

from sqlalchemy import Column, Integer, Date, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database import Base
from .employee import Employee


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    # Link to employees table
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)

    # The calendar date this attendance belongs to
    attendance_date = Column(Date, nullable=False, index=True)

    # "Present", "PaidLeave", "UnpaidLeave"
    status = Column(String(50), nullable=False)

    # Ensure only one row per employee per date
    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uix_employee_date"),
    )

    # (Optional) relationship, not strictly needed but handy
    employee = relationship(Employee, lazy="joined")
