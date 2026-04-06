"""
Auth Router — Registration and Login endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from services.auth_service import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_user_by_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = get_user_by_email(db, req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if req.role not in ("client", "musician"):
        raise HTTPException(status_code=400, detail="Role must be 'client' or 'musician'")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    # Auto-assign a client/musician ID
    if req.role == "client":
        count = db.query(User).filter(User.role == "client").count()
        user.client_id = f"C{count + 301:03d}"  # start after seeded data
    else:
        count = db.query(User).filter(User.role == "musician").count()
        user.musician_id = f"M{count + 501:03d}"

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
