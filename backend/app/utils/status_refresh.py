from datetime import date
from sqlalchemy.orm import Session

from ..models.employee import Employee


def refresh_employee_statuses(today: date, db: Session) -> None:
    """
    For all employees where status_change_date == today
    and upcoming_status is set, move upcoming_status into
    current_status and clear the future fields.
    """
    employees_to_update = (
        db.query(Employee)
        .filter(
            Employee.status_change_date == today,
            Employee.upcoming_status.isnot(None),
        )
        .all()
    )

    for emp in employees_to_update:
        emp.current_status = emp.upcoming_status
        emp.upcoming_status = None
        emp.status_change_date = None

    db.commit()
