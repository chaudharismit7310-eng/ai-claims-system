from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.models import (
    user_model,
    claim_model,
    policy_model,
    vehicle_model
)

from app.routes import (
    claim_routes,
    policy_routes,
    auth_routes,
    analytics_routes,
    vehicle_routes,
    admin_routes
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="AI Claims Validation System")

# Enable CORS (Explicit Credentials Support)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(claim_routes.router)
app.include_router(policy_routes.router)
app.include_router(analytics_routes.router)
app.include_router(vehicle_routes.router)
app.include_router(admin_routes.router)

# Serve uploaded files & static assets
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Home route
@app.get("/")
def home():
    return {"message": "AI Claims System Running"}

# Health check route
@app.get("/health")
def health():
    return {"status": "healthy"}