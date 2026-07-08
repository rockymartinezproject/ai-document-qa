"""Authentication endpoints for registration, login, and current user."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.base import get_db
from app.db.models import User
from app.models.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.models.response import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger("auth_api")


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


@router.post(
    "/register",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    """Create a new user account."""
    request_id = getattr(request.state, "request_id", None)

    existing = await _get_user_by_email(session, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=body.email.lower().strip(),
        hashed_password=get_password_hash(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info("Registered new user %s", user.id)
    return APIResponse(
        success=True,
        data=UserOut.model_validate(user),
        request_id=request_id,
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login_json(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """Authenticate with email/password and receive a JWT."""
    request_id = getattr(request.state, "request_id", None)

    user = await _get_user_by_email(session, body.email.lower().strip())
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.id})
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            user=UserOut.model_validate(user),
        ),
        request_id=request_id,
    )


@router.post("/token", response_model=APIResponse[TokenResponse])
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """OAuth2 password flow token endpoint (used by Swagger UI)."""
    request_id = getattr(request.state, "request_id", None)

    user = await _get_user_by_email(session, form_data.username.lower().strip())
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.id})
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            user=UserOut.model_validate(user),
        ),
        request_id=request_id,
    )


@router.get("/me", response_model=APIResponse[UserOut])
async def me(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Return the currently authenticated user."""
    request_id = getattr(request.state, "request_id", None)
    return APIResponse(
        success=True,
        data=UserOut.model_validate(user),
        request_id=request_id,
    )
