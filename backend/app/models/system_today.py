from datetime import date

from sqlalchemy import Column, Integer, Date
from ..database import Base


class SystemToday(Base):
    """
    Single-row table to store the globally locked 'Today' date.

    We will always use id=1.
    - manual_today: the latest 'Today' the system has accepted.
    """
    __tablename__ = "system_today"

    id = Column(Integer, primary_key=True, index=True)
    manual_today = Column(Date, nullable=True)
