from datetime import date
from typing import Optional

from pydantic import BaseModel


class SystemTodayOut(BaseModel):
    """
    Response shape for GET /system/today

    Example:
    { "today": "2025-12-02" }
    or
    { "today": null } if not set yet
    """
    today: Optional[date]


class SystemTodayUpdate(BaseModel):
    """
    Request body for POST /system/today

    Example:
    { "today": "2025-12-02" }
    """
    today: date
