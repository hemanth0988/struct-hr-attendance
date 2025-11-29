from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .models import employee as employee_model
from .models import attendance as attendance_model
from .routers import employees as employees_router
from .routers import attendance as attendance_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow frontend (any origin for now – simple for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # later we can restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Struct HR Attendance API running"}


# Include routes
app.include_router(employees_router.router)
app.include_router(attendance_router.router)
