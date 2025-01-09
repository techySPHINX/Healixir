from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import Lifespan

from app.database import init_db
from app.api.v1.endpoints import auth, hospitals, health_records, appointments, telemedicine

# Define the lifespan function
def lifespan():
    async def start_app():
        # Application startup logic
        init_db()  # Initialize the database
        print("Application startup completed!")

    async def stop_app():
        # Application shutdown logic (optional)
        print("Application shutdown completed!")

    return start_app, stop_app

# Create the FastAPI app with the lifespan context
app = FastAPI(
    title="HealXir",
    description="API for managing authentication and other healthcare functionalities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=Lifespan(lifespan)
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(hospitals.router, prefix="/api/v1/hospitals", tags=["Hospitals"])
app.include_router(health_records.router, prefix="/api/v1/health_records", tags=["Health Records"])
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(telemedicine.router, prefix="/api/v1/telemedicine", tags=["Telemedicine"])

# Root endpoint to verify the API is running
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the HealXir API!"}
