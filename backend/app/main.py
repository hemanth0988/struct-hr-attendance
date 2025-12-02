from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .models import employee as employee_model  # ensure models are registered
from .models import attendance as attendance_model
from .routers import employees, attendance, admin_reset
from .routers import employees, attendance, admin, system_today
# or if using absolute import style:
# from backend.app.routers import employees, attendance, admin, system_today

# Create tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Struct HR Attendance API")

# CORS – allow everything for now (you’re loading HTML from file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Struct HR Attendance API running"}


# API routers
app.include_router(employees.router)
app.include_router(attendance.router)
app.include_router(admin_reset.router)
app.include_router(system_today.router)

