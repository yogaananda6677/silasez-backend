import os
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.crud.user import update_user, get_all_pakar
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UpdateProfileRequest

UPLOAD_DIR = "uploads/photos"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


class UserService:

    def __init__(self, db: Session):
        self.db = db

    def get_profile(self, user: User) -> User:
        return user

    def update_profile(self, user: User, data: UpdateProfileRequest) -> User:
        updates = data.model_dump(exclude_unset=True, exclude_none=True)

        if not updates:
            return user

        return update_user(self.db, user, **updates)

    def change_password(self, user: User, data: ChangePasswordRequest) -> User:
        if not verify_password(data.old_password, user.password):
            raise ValueError("Password lama salah.")

        if verify_password(data.new_password, user.password):
            raise ValueError("Password baru tidak boleh sama dengan password lama.")

        return update_user(
            self.db,
            user,
            password=hash_password(data.new_password),
        )

    def upload_photo(self, user: User, file: UploadFile) -> User:
        ext = os.path.splitext(file.filename or "")[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                "Format foto tidak didukung. Gunakan JPG, PNG, atau WEBP."
            )

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        filename = f"{user.id}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        contents = file.file.read()

        if len(contents) > MAX_PHOTO_SIZE_BYTES:
            raise ValueError("Ukuran foto maksimal 2MB.")

        with open(filepath, "wb") as f:
            f.write(contents)

        # Hapus foto lama kalau ada, biar tidak menumpuk file sampah
        if user.photo_url:
            old_path = user.photo_url.replace("/static/", "", 1)
            if os.path.exists(old_path) and old_path.startswith(UPLOAD_DIR):
                os.remove(old_path)

        photo_url = f"/static/photos/{filename}"

        return update_user(self.db, user, photo_url=photo_url)

    def list_pakar(self):
        return get_all_pakar(self.db)