from datetime import date

from sqlalchemy import Column, Integer, String, Date, Numeric
from ..database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    # Auto-generated code: EMP01, EMP02, ...
    emp_code = Column(String(20), unique=True, nullable=False, index=True)

    # Basic identity
    name = Column(String(255), nullable=False)
    joining_date = Column(Date, nullable=False)

    # Status logic
    current_status = Column(String(20), nullable=False)          # Active, Inactive, Offboarded, Vacation
    status_change_date = Column(Date, nullable=True)             # When upcoming_status takes effect
    upcoming_status = Column(String(20), nullable=True)          # Next status (Active/Offboarded/Vacation)

    # Salary components (monthly)
    basic_pay_monthly = Column(Numeric(10, 2), nullable=False)
    transport_monthly = Column(Numeric(10, 2), nullable=False)
    accommodation_monthly = Column(Numeric(10, 2), nullable=False)
    other_monthly = Column(Numeric(10, 2), nullable=False)

    # Daily rates
    paid_leave_daily = Column(Numeric(10, 2), nullable=False)
    vacation_pay_daily = Column(Numeric(10, 2), nullable=False)

    # ⭐ Total monthly – this is the column MySQL was complaining about
    total_salary_monthly = Column(Numeric(10, 2), nullable=False)
