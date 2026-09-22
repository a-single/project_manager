from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user, require_pm_or_admin
from ..database import get_db
from ..helpers import can_manage_project, is_late_task, is_overdue_task, is_project_related
from ..schemas import OverdueCount, StatRecord

router = APIRouter(prefix="/stats", tags=["stats"])


def _parse_dt(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"{field} 时间格式不合法，应为 YYYY-MM-DD 或 ISO 格式"
            )


def _day_range(value: str, field: str):
    """前端日期选择器传 YYYY-MM-DD，补充为当天起止。若带时分秒则原样使用。"""
    if len(value) <= 10:
        dt = datetime.strptime(value, "%Y-%m-%d")
        if field == "start":
            return dt
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return _parse_dt(value, field)


@router.get("/task-records", response_model=List[StatRecord])
def task_records(
    project_id: int,
    start: str,
    end: str,
    user_id: Optional[int] = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not is_project_related(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权访问该项目")
    start_dt = _day_range(start, "start")
    end_dt = _day_range(end, "end")
    if start_dt > end_dt:
        raise HTTPException(status_code=400, detail="开始时间不能晚于结束时间")

    q = (
        db.query(models.Task)
        .filter(
            models.Task.project_id == project_id,
            models.Task.status.in_(
                [models.TASK_STATUS_COMPLETED, models.TASK_STATUS_APPROVED]
            ),
            models.Task.completed_at >= start_dt,
            models.Task.completed_at <= end_dt,
        )
        .order_by(models.Task.completed_at.asc())
    )
    if user_id is not None:
        q = q.filter(models.Task.assignee_id == user_id)
    rows = q.all()

    result = []
    for t in rows:
        duration = None
        if t.completed_at is not None:
            duration = int((t.completed_at - t.created_at).total_seconds() // 60)
        result.append(
            StatRecord(
                task_id=t.id,
                title=t.title,
                status=t.status,
                assignee_id=t.assignee_id,
                assignee_name=t.assignee.username if t.assignee else "",
                assignee_role_label=models.ROLE_LABELS.get(t.assignee.role, "") if t.assignee else "",
                project_id=t.project_id,
                project_name=t.project.name if t.project else "",
                created_at=t.created_at,
                completed_at=t.completed_at,
                duration_minutes=duration,
            )
        )
    return result


@router.get("/overdue-counts", response_model=List[OverdueCount])
def overdue_counts(
    project_id: int,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    """每个工作人员的超时任务数量（实时计算：未完成且超过预计完成时间 + 已确认但延毕的任务）"""
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权访问该项目")
    rows = (
        db.query(models.Task)
        .filter(
            models.Task.project_id == project_id,
            models.Task.due_at.isnot(None),
        )
        .all()
    )
    agg = {}
    for t in rows:
        overdue = is_overdue_task(t) or is_late_task(t)
        if not overdue:
            continue
        name = t.assignee.username if t.assignee else ""
        if t.assignee_id not in agg:
            agg[t.assignee_id] = {"assignee_name": name, "count": 0}
        agg[t.assignee_id]["count"] += 1
    return [
        OverdueCount(assignee_id=k, assignee_name=v["assignee_name"], count=v["count"])
        for k, v in sorted(agg.items(), key=lambda x: -x[1]["count"])
    ]