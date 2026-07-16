"""Admin-only user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.core.limiter import limiter
from app.core.logging import get_logger
from app.db.models import User
from app.models.auth import UserOut
from app.models.response import APIResponse

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger("admin_api")


class UserStatusUpdate(BaseModel):
    """Request body to update a user's active/superuser status."""

    is_active: bool | None = None
    is_superuser: bool | None = None


@router.get("/users", response_model=APIResponse[list[UserOut]])
@limiter.limit("30/minute")
async def list_users(
    request: Request,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all registered users (admin only)."""
    request_id = getattr(request.state, "request_id", None)

    result = await session.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    return APIResponse(
        success=True,
        data=[UserOut.model_validate(u) for u in users],
        request_id=request_id,
    )


@router.patch("/users/{user_id}", response_model=APIResponse[UserOut])
@limiter.limit("30/minute")
async def update_user_status(
    request: Request,
    user_id: str,
    body: UserStatusUpdate,
    session: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Activate/deactivate or promote/demote a user (admin only)."""
    request_id = getattr(request.state, "request_id", None)

    if user_id == admin_user.id and body.is_active is False:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot deactivate their own account",
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.is_active is not None:
        user.is_active = body.is_active
    if body.is_superuser is not None:
        user.is_superuser = body.is_superuser

    await session.commit()
    await session.refresh(user)

    logger.info(
        "Admin %s updated user %s: is_active=%s is_superuser=%s",
        admin_user.id,
        user_id,
        user.is_active,
        user.is_superuser,
    )

    return APIResponse(
        success=True,
        data=UserOut.model_validate(user),
        request_id=request_id,
    )
