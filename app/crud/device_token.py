from uuid import UUID

from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken


def upsert(db: Session, user_id: UUID, token: str, platform: str) -> DeviceToken:
    item = db.query(DeviceToken).filter(DeviceToken.token == token).first()
    if item is None:
        item = DeviceToken(user_id=user_id, token=token, platform=platform)
        db.add(item)
    else:
        item.user_id = user_id
        item.platform = platform
    db.commit()
    db.refresh(item)
    return item


def delete(db: Session, user_id: UUID, token: str) -> bool:
    count = (
        db.query(DeviceToken)
        .filter(DeviceToken.user_id == user_id, DeviceToken.token == token)
        .delete(synchronize_session=False)
    )
    db.commit()
    return count > 0


def list_tokens(db: Session, user_id: UUID) -> list[str]:
    return [
        row[0]
        for row in db.query(DeviceToken.token)
        .filter(DeviceToken.user_id == user_id)
        .all()
    ]


def delete_tokens(db: Session, tokens: list[str]) -> None:
    if not tokens:
        return
    db.query(DeviceToken).filter(DeviceToken.token.in_(tokens)).delete(
        synchronize_session=False
    )
    db.commit()
