from fastapi import FastAPI

from .database import Base, engine
from .models import employee as employee_model
from .routers import employees as employees_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Struct HR Attendance API running"}


# Include employee routes
app.include_router(employees_router.router)
