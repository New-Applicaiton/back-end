from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import models
import schemas
import auth
from database import SessionLocal, engine
import crud

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Dashboard API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth endpoints
@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.authenticate_user(db, email=user.email, password=user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email,
            "username": db_user.username
        }
    }

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

# Dashboard endpoints
@app.get("/dashboard/stats")
def get_dashboard_stats(current_user: schemas.User = Depends(auth.get_current_user)):
    # Example dashboard data
    return {
        "total_users": 150,
        "active_users": 42,
        "monthly_revenue": 12500,
        "growth_rate": 15.5
    }

@app.get("/dashboard/recent-activities")
def get_recent_activities(current_user: schemas.User = Depends(auth.get_current_user)):
    # Example recent activities
    return [
        {"id": 1, "user": "John Doe", "action": "Logged in", "time": "2 minutes ago"},
        {"id": 2, "user": "Jane Smith", "action": "Updated profile", "time": "15 minutes ago"},
        {"id": 3, "user": "Bob Wilson", "action": "Created report", "time": "1 hour ago"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
