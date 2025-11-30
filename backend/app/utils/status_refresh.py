from datetime import date
from sqlalchemy.orm import Session

from ..models.employee import Employee


def refresh_employee_statuses(today: date, db: Session) -> None:
    """
    1) Apply any scheduled status changes:
       - if status_change_date == today and upcoming_status is set:
         move upcoming_status into current_status and clear the future fields.

    2) Auto-activate future joinees:
       - if current_status == 'Inactive' and joining_date <= today:
         set current_status = 'Active'.
    """

    # 1) Scheduled status changes (Offboarded / Vacation / Active, etc.)
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

    # 2) Inactive -> Active when joining_date reached (using manual 'today')
    inactive_to_activate = (
        db.query(Employee)
        .filter(
            Employee.current_status == "Inactive",
            Employee.joining_date <= today,
        )
        .all()
    )

    for emp in inactive_to_activate:
        emp.current_status = "Active"

    db.commit()
