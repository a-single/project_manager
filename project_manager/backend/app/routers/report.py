from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..helpers import serialize_task
from ..schemas import TaskOut

router = APIRouter(prefix="/report", tags=["report"])


def _day_range(value: str, field: str) -> datetime:
    try:
        if len(value) <= 10:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt if field == "start" else dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"{field} 时间格式不合法，应为 YYYY-MM-DD 或 ISO 格式"
        )


@router.get("/mine", response_model=List[TaskOut])
def my_report(
    start: str,
    end: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户在时间段内的任务记录：派发时间在区间内，或完成时间在区间内。"""
    start_dt = _day_range(start, "start")
    end_dt = _day_range(end, "end")
    rows = (
        db.query(models.Task)
        .filter(
            models.Task.assignee_id == user.id,
            or_(
                models.Task.created_at >= start_dt,
                models.Task.completed_at >= start_dt,
            ),
            models.Task.created_at <= end_dt,
        )
        .order_by(models.Task.created_at.desc())
        .all()
    )
    return [TaskOut(**serialize_task(db, t)) for t in rows]