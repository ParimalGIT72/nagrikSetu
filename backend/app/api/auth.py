from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.config import settings
from app.db.database import get_db
from app.models.complaint import Complaint
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    RegistrationRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.complaint import ComplaintListResponse
from app.services.authentication import (
    create_access_token,
    hash_password,
    normalize_email,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/hour")
def register(
    request: Request,
    registration: RegistrationRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(str(registration.email))
    user = User(
        email=email,
        password_hash=hash_password(registration.password.get_secret_value()),
        role="citizen",
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) != "23505":
            raise
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(str(credentials.email))
    user = db.query(User).filter(User.email == email).first()
    password = credentials.password.get_secret_value()
    if user is None:
        verify_password(password, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(user)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("/me/complaints", response_model=ComplaintListResponse)
def get_my_complaints(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint).filter(Complaint.user_id == user.id)
    total = query.count()
    items = query.order_by(Complaint.created_at.desc()).offset(offset).limit(limit).all()
    return ComplaintListResponse(total=total, items=items)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.token_version += 1
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)