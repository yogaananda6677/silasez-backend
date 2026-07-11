from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def get_by_email(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def get_by_id(
    db: Session,
    user_id: UUID,
) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )



def create_user(
    db: Session,
    fullname: str,
    email: str,
    password: str,
    phone: str,
    role: UserRole,
) -> User:

    user = User(
        fullname=fullname,
        email=email,
        password=hash_password(password),
        phone=phone, 
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    user: User,
    **kwargs,
) -> User:

    for key, value in kwargs.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


def delete_user(
    db: Session,
    user: User,
):

    user.is_deleted = True

    db.commit()

    return user

def get_all_pakar(
    db: Session,
) -> list[User]:

    return (
        db.query(User)
        .filter(
            User.role == UserRole.PAKAR,
            User.is_active.is_(True),
        )
        .order_by(User.fullname.asc())
        .all()
    )