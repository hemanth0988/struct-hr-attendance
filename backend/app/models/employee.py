from sqlalchemy import Column, Integer, String, Date, DECIMAL
from ..database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    emp_code = Column(String(10), unique=True, index=True)  # EMP01, EMP02...

    name = Column(String(100), nullable=False)
    joining_date = Column(Date, nullable=False)

    # Status-related (will be controlled via list screen + "today" logic)
    current_status = Column(String(20), default="Active")      # e.g. Active / Inactive / OnLeave
    status_change_date = Column(Date, nullable=True)
    upcoming_status = Column(String(20), nullable=True)

    # Monthly salary components
    basic_pay_monthly = Column(DECIMAL(10, 2), nullable=False)
    transport_monthly = Column(DECIMAL(10, 2), nullable=False)
    accommodation_monthly = Column(DECIMAL(10, 2), nullable=False)
    other_monthly = Column(DECIMAL(10, 2), nullable=False)
    total_salary_monthly = Column(DECIMAL(10, 2), nullable=False)

    # Leave-related daily fields (user editable)
    paid_leave_daily = Column(DECIMAL(10, 2), nullable=False)
    vacation_pay_daily = Column(DECIMAL(10, 2), nullable=False)
