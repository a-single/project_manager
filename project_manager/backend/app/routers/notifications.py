from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..helpers import serialize_notification
from ..schemas import MessageOut, NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user.id)
        .order_by(models.Notification.created_at.desc(), models.Notification.id.desc())
    )
    if unread_only:
        q = q.filter(models.Notification.is_read == False)  # noqa: E712
    rows = q.limit(50).all()
    return [NotificationOut(**serialize_notification(db, n)) for n in rows]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == user.id,
            models.Notification.is_read == False,  # noqa: E712
        )
        .count()
    )
    return UnreadCountOut(count=count)


@router.put("/{notification_id}/read", response_model=MessageOut)
def mark_read(
    notification_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.get(models.Notification, notification_id)
    if n is None or n.user_id != user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="消息不存在")
    n.is_read = True
    db.commit()
    return MessageOut(message="ok")


@router.put("/read-all", response_model=MessageOut)
def mark_all_read(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == user.id,
        models.Notification.is_read == False,  # noqa: E712
    ).update({models.Notification.is_read: True})
    db.commit()
    return MessageOut(message="ok")