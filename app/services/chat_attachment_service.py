import os
import uuid
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.enums import MessageType


@dataclass(frozen=True)
class StoredChatAttachment:
    url: str
    message_type: MessageType
    display_name: str
    content_type: str
    contents: bytes


class ChatAttachmentService:
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
    DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
    MAX_IMAGE_BYTES = 10 * 1024 * 1024
    MAX_VIDEO_BYTES = 25 * 1024 * 1024
    MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
    UPLOAD_DIR = "uploads/chat"

    async def store(self, room_id: str, file: UploadFile) -> StoredChatAttachment:
        original_name = os.path.basename(file.filename or "lampiran")
        extension = os.path.splitext(original_name)[1].lower()
        content_type = (file.content_type or "application/octet-stream").lower()

        if extension in self.IMAGE_EXTENSIONS and content_type.startswith("image/"):
            message_type = MessageType.IMAGE
            max_bytes = self.MAX_IMAGE_BYTES
        elif extension in self.VIDEO_EXTENSIONS and content_type.startswith("video/"):
            message_type = MessageType.VIDEO
            max_bytes = self.MAX_VIDEO_BYTES
        elif extension in self.DOCUMENT_EXTENSIONS:
            message_type = MessageType.FILE
            max_bytes = self.MAX_DOCUMENT_BYTES
        else:
            raise ValueError(
                "Format tidak didukung. Gunakan JPG, PNG, WEBP, MP4, MOV, "
                "WEBM, PDF, DOC, DOCX, atau TXT."
            )

        contents = await file.read(max_bytes + 1)
        if len(contents) > max_bytes:
            size_mb = max_bytes // (1024 * 1024)
            raise ValueError(f"Ukuran file maksimal {size_mb}MB.")
        if not contents:
            raise ValueError("File tidak boleh kosong.")

        directory = os.path.join(self.UPLOAD_DIR, room_id)
        os.makedirs(directory, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}{extension}"
        path = os.path.join(directory, stored_name)
        with open(path, "wb") as destination:
            destination.write(contents)

        return StoredChatAttachment(
            url=f"/static/chat/{room_id}/{stored_name}",
            message_type=message_type,
            display_name=original_name[:200],
            content_type=content_type,
            contents=contents,
        )
