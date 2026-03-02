import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
import app.models as models
from app.routers import auth, analyze, subscriptions, payments, affiliates, admin

# Create all tables in the database (For dev only! Use Alembic for prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Softi Analyze API",
    description="Core backend API for Softi Analyze ecosystem",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth.router)
app.include_router(auth.consent_router)
app.include_router(analyze.router)
app.include_router(subscriptions.router)
app.include_router(payments.router)
app.include_router(affiliates.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Softi Analyze API is running", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
