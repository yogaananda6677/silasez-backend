from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.crud.user import create_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    def __init__(self, db: Session):
        self.db = db

    def register(
        self,
        data: RegisterRequest,
    ):

        user = (
            self.db.query(User)
            .filter(User.email == data.email)
            .first()
        )

        if user:
            raise ValueError("Email sudah digunakan.")

        return create_user(
            self.db,
            fullname=data.fullname,
            email=data.email,
            password=data.password,
            phone=data.phone,
            role=UserRole.PETERNAK,
        )


    def login(
        self,
        data: LoginRequest,
    ):

        user = (
            self.db.query(User)
            .filter(User.email == data.email)
            .first()
        )

        if not user:
            raise ValueError("Email atau password salah.")

        if not verify_password(
            data.password,
            user.password,
        ):
            raise ValueError("Email atau password salah.")

        token = create_access_token(
            {
                "sub": str(user.id),
                "role": user.role.value,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }