from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from database import init_db
from routers import common, reception, doctor, radiology, pharmacy, admin, api

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("✅ Database initialized successfully")
    print("🏥 Hospital Information System is ready!")
    print("📝 Access the system at: http://localhost:8000")
    print("⚠️  Don't forget to create the first admin user using initial_admin.py")
    yield
    # Shutdown (if needed)

# Initialize FastAPI app
app = FastAPI(
    title="Simple Hospital Information System",
    description="A modern, lightweight Hospital Information System",
    version="2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(common.router)
app.include_router(reception.router)
app.include_router(doctor.router)
app.include_router(radiology.router)
app.include_router(pharmacy.router)
app.include_router(admin.router)
app.include_router(api.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
