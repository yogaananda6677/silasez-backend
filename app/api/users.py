from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.dependencies import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UserProfileResponse,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


@router.get("/me", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.get_profile(current_user)


@router.patch("/me", response_model=UserProfileResponse)
def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.update_profile(current_user, data)


@router.post("/me/change-password", response_model=UserProfileResponse)
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)

    try:
        return service.change_password(current_user, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/photo", response_model=UserProfileResponse)
def upload_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)

    try:
        return service.upload_photo(current_user, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get(
    "/pakar",
    response_model=list[UserResponse],
)
def list_pakar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = UserService(db)

    return service.list_pakar()