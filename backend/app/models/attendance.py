from sqlalchemy import Column, Integer, Date, String, ForeignKey, UniqueConstraint
from ..database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    attendance_date = Column(Date, nullable=False)

    # Allowed: Present, PaidLeave, UnpaidLeave
    status = Column(String(20), nullable=False)

    # Ensure only 1 attendance entry per employee per date
    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_employee_date"),
    )
