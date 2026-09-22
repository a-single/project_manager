from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models


def ensure_unique_username(db: Session, username: str, exclude_id: Optional[int] = None):
    q = db.query(models.User).filter(models.User.username == username)
    if exclude_id is not None:
        q = q.filter(models.User.id != exclude_id)
    if q.first() is not None:
        raise HTTPException(status_code=400, detail=f"用户名 {username} 已存在")


def serialize_user(u: models.User):
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name or "",
        "email": u.email or "",
        "phone": u.phone or "",
        "role": u.role,
        "role_label": models.ROLE_LABELS.get(u.role, u.role),
        "created_at": u.created_at,
    }


def serialize_project(db: Session, p: models.Project):
    member_count = (
        db.query(models.ProjectMember)
        .filter(models.ProjectMember.project_id == p.id)
        .count()
    )
    total_tasks = (
        db.query(models.Task).filter(models.Task.project_id == p.id).count()
    )
    pending_tasks = (
        db.query(models.Task)
        .filter(
            models.Task.project_id == p.id,
            models.Task.status == models.TASK_STATUS_PENDING,
        )
        .count()
    )
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description or "",
        "manager_id": p.manager_id,
        "manager_name": p.manager.username if p.manager else "",
        "created_at": p.created_at,
        "archived": bool(p.archived),
        "member_count": member_count,
        "task_count": total_tasks,
        "pending_task_count": pending_tasks,
    }


def is_overdue_task(t: models.Task) -> bool:
    """实时超时判定：未完成（待处理/已驳回）且已过预计完成时间"""
    if t.status not in (models.TASK_STATUS_PENDING, models.TASK_STATUS_REJECTED):
        return False
    if t.due_at is None:
        return False
    return datetime.now() > t.due_at


def is_late_task(t: models.Task) -> bool:
    """已延毕判定：经理已确认，但实际完成时间晚于预计完成时间"""
    if t.status != models.TASK_STATUS_APPROVED:
        return False
    if t.due_at is None or t.completed_at is None:
        return False
    return t.completed_at > t.due_at


def serialize_task(db: Session, t: models.Task):
    duration = None
    if t.completed_at is not None:
        duration = int(
            (t.completed_at - t.created_at).total_seconds() // 60
        )
    overdue = is_overdue_task(t)
    late = is_late_task(t)
    if overdue:
        eff_status, eff_label = models.TASK_STATUS_OVERDUE, models.TASK_STATUS_LABELS[models.TASK_STATUS_OVERDUE]
    elif late:
        eff_status, eff_label = models.TASK_STATUS_LATE, models.TASK_STATUS_LABELS[models.TASK_STATUS_LATE]
    else:
        eff_status, eff_label = t.status, models.TASK_STATUS_LABELS.get(t.status, t.status)
    return {
        "id": t.id,
        "project_id": t.project_id,
        "project_name": t.project.name if t.project else "",
        "title": t.title,
        "description": t.description or "",
        "assignee_id": t.assignee_id,
        "assignee_name": t.assignee.username if t.assignee else "",
        "assignee_role_label": models.ROLE_LABELS.get(t.assignee.role, "") if t.assignee else "",
        "assigner_id": t.assigner_id,
        "assigner_name": t.assigner.username if t.assigner else "",
        "attachment_required": t.attachment_required,
        "status": eff_status,
        "status_label": eff_label,
        "comment": t.comment or "",
        "review_comment": t.review_comment or "",
        "created_at": t.created_at,
        "completed_at": t.completed_at,
        "due_at": t.due_at,
        "is_milestone": bool(t.is_milestone),
        "is_overdue": overdue,
        "is_late": late,
        "duration_minutes": duration,
        "attachments": [
            {
                "id": a.id,
                "file_name": a.file_name,
                "file_size": a.file_size,
                "uploaded_at": a.uploaded_at,
                "uploader_name": a.uploader.username if a.uploader else "",
            }
            for a in t.attachments
        ],
    }


def serialize_notification(db: Session, n: models.Notification):
    return {
        "id": n.id,
        "type": n.type,
        "message": n.message,
        "task_id": n.task_id,
        "from_user_id": n.from_user_id,
        "from_user_name": n.from_user.username if n.from_user else "",
        "task_title": n.task.title if n.task else "",
        "is_read": n.is_read,
        "created_at": n.created_at,
    }


def is_project_related(db: Session, project_id: int, user: models.User) -> bool:
    """项目可访问性：管理员、项目负责人始终可看；归档项目仅负责人/管理员可看，普通成员不可见。"""
    if user.role == models.ROLE_ADMIN:
        return True
    p = db.get(models.Project, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if p.archived:
        # 已归档：只有项目经理能继续查看（只读）
        return p.manager_id == user.id
    if p.manager_id == user.id:
        return True
    member = (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user.id,
        )
        .first()
    )
    return member is not None


def can_manage_project(db: Session, project_id: int, user: models.User) -> bool:
    p = db.get(models.Project, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return user.role == models.ROLE_ADMIN or p.manager_id == user.id


def assert_project_open(db: Session, project_id: int, user: models.User):
    """归档项目锁定所有写操作：派发/提交/确认/驳回/加删成员。
    仅校验项目归属/存在与归档状态；管理权限由各接口自身的
    can_manage_project / _assert_reviewer / require_pm_or_admin 负责。"""
    if user is None:
        raise HTTPException(status_code=401, detail="登录已失效")
    p = db.get(models.Project, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if p.archived:
        raise HTTPException(status_code=403, detail="项目已归档，所有任务状态已锁定，仅可查看")