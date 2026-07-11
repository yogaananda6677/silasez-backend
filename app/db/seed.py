from sqlalchemy.orm import Session

from app.models.user import User
from app.core.enums import UserRole
from app.core.security import hash_password


DEFAULT_ADMIN = {
    "fullname": "Administrator",
    "email": "admin@silasez.com",
    "password": "Admin123!",
    "phone": "081234567890",
}

def seed_admin(db: Session):

    admin = (
        db.query(User)
        .filter(User.email == DEFAULT_ADMIN["email"])
        .first()
    )

    if admin:
        return

    admin = User(
        fullname=DEFAULT_ADMIN["fullname"],
        email=DEFAULT_ADMIN["email"],
        phone=DEFAULT_ADMIN["phone"],
        password=hash_password(
            DEFAULT_ADMIN["password"]
        ),
        role=UserRole.ADMIN,
        is_active=True,
    )

    db.add(admin)
    db.commit()

    print("✅ Default admin created")