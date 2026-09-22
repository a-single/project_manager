import uuid
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user, require_pm_or_admin
from ..config import MAX_UPLOAD_SIZE, UPLOAD_DIR
from ..database import get_db
from ..helpers import (
    assert_project_open,
    can_manage_project,
    is_project_related,
    serialize_task,
)
from ..schemas import MessageOut, TaskCreate, TaskOut

router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskOut)
def create_task(
    project_id: int,
    body: TaskCreate,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    assert_project_open(db, project_id, user)
    member = (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == body.assignee_id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=400, detail="被派发人不是该项目成员")
    t = models.Task(
        project_id=project_id,
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        assigner_id=user.id,
        attachment_required=body.attachment_required,
        due_at=body.due_at,
        is_milestone=body.is_milestone,
    )
    db.add(t)
    db.flush()
    assignee = db.get(models.User, body.assignee_id)
    try:
        notification = models.Notification(
            user_id=body.assignee_id,
            type=models.NOTIF_TASK_ASSIGNED,
            message=f"{user.username} 在项目「{t.project.name}」下给你派发了新任务《{t.title}》",
            task_id=t.id,
            from_user_id=user.id,
        )
        db.add(notification)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(t)
    return TaskOut(**serialize_task(db, t))


@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    scope: str = "mine",
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.Task)
    if project_id is not None:
        # 显式指定项目（如项目详情/归档项目详情）：先校验可访问性，返回该项目全部任务
        if not is_project_related(db, project_id, user):
            raise HTTPException(status_code=403, detail="无权访问该项目")
        rows = (
            q.filter(models.Task.project_id == project_id)
            .order_by(models.Task.created_at.desc())
            .all()
        )
        return [TaskOut(**serialize_task(db, t)) for t in rows]

    # 列表（首页/我的任务等）：不展示已归档项目的任务
    q = q.join(models.Project).filter(models.Project.archived == False)  # noqa: E712
    if scope == "mine":
        q = q.filter(models.Task.assignee_id == user.id)
    elif scope == "managed":
        if user.role == models.ROLE_ADMIN:
            pass
        else:
            managed_project_ids = [
                r[0]
                for r in db.query(models.Project.id).filter(
                    models.Project.manager_id == user.id,
                    models.Project.archived == False,  # noqa: E712
                )
            ]
            q = q.filter(models.Task.project_id.in_(managed_project_ids or [-1]))
    elif scope == "member":  # 项目成员视角的项目全部任务
        if user.role == models.ROLE_ADMIN:
            pass
        else:
            my_project_ids = [
                r[0]
                for r in db.query(models.ProjectMember.project_id)
                .join(models.Project, models.Project.id == models.ProjectMember.project_id)
                .filter(
                    models.ProjectMember.user_id == user.id,
                    models.Project.archived == False,  # noqa: E712
                )
            ]
            q = q.filter(
                (models.Task.project_id.in_(my_project_ids or [-1]))
                | (
                    db.query(models.Project.manager_id)
                    .filter(models.Project.id == models.Task.project_id)
                    .filter(models.Project.manager_id == user.id)
                    .filter(models.Project.archived == False)  # noqa: E712
                    .exists()
                )
            )
    else:
        raise HTTPException(status_code=400, detail="scope 参数不合法")
    rows = q.order_by(models.Task.created_at.desc()).all()
    return [TaskOut(**serialize_task(db, t)) for t in rows]


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.get(models.Task, task_id)
    if t is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not is_project_related(db, t.project_id, user):
        raise HTTPException(status_code=403, detail="无权访问该任务")
    return TaskOut(**serialize_task(db, t))


@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: int,
    comment: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.get(models.Task, task_id)
    if t is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    assert_project_open(db, t.project_id, user)
    if t.assignee_id != user.id:
        raise HTTPException(status_code=403, detail="只有被派发人能完成该任务")
    if t.status not in (models.TASK_STATUS_PENDING, models.TASK_STATUS_REJECTED):
        raise HTTPException(status_code=400, detail="当前状态下不能提交工作")

    has_files = any(f and f.filename for f in files)
    if not has_files and not comment.strip():
        raise HTTPException(status_code=400, detail="未提交附件时，留言记录为必填")

    from datetime import datetime

    try:
        for f in files:
            if not f.filename:
                continue
            content = f.file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=400, detail=f"附件 {f.filename} 超过 20MB 限制")
            suffix = Path(f.filename).suffix[:20]
            stored_name = f"{uuid.uuid4().hex}{suffix}"
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            target = UPLOAD_DIR / stored_name
            target.write_bytes(content)
            db.add(
                models.TaskAttachment(
                    task_id=t.id,
                    file_name=f.filename,
                    stored_name=stored_name,
                    file_size=len(content),
                    uploader_id=user.id,
                )
            )

        t.status = models.TASK_STATUS_COMPLETED
        t.comment = comment.strip()
        t.review_comment = ""
        t.completed_at = datetime.now()
        notification = models.Notification(
            user_id=t.assigner_id,
            type=models.NOTIF_TASK_COMPLETED,
            message=f"{user.username} 完成了任务《{t.title}》",
            task_id=t.id,
            from_user_id=user.id,
        )
        db.add(notification)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    db.refresh(t)
    return TaskOut(**serialize_task(db, t))


def _assert_reviewer(t: models.Task, user: models.User):
    """任务派发人（项目经理）或管理员可执行确认/驳回"""
    if t is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if user.role != models.ROLE_ADMIN and t.assigner_id != user.id:
        raise HTTPException(status_code=403, detail="只有任务派发人能确认或驳回")


@router.post("/tasks/{task_id}/approve", response_model=TaskOut)
def approve_task(
    task_id: int,
    comment: str = Form(""),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.get(models.Task, task_id)
    _assert_reviewer(t, user)
    assert_project_open(db, t.project_id, user)
    if t.status != models.TASK_STATUS_COMPLETED:
        raise HTTPException(status_code=400, detail="只有待确认的任务可以确认完成")
    t.status = models.TASK_STATUS_APPROVED
    if comment.strip():
        t.review_comment = comment.strip()
    db.add(
        models.Notification(
            user_id=t.assignee_id,
            type=models.NOTIF_TASK_APPROVED,
            message=f"{user.username} 已确认你的任务《{t.title}》完成",
            task_id=t.id,
            from_user_id=user.id,
        )
    )
    db.commit()
    db.refresh(t)
    return TaskOut(**serialize_task(db, t))


@router.post("/tasks/{task_id}/reject", response_model=TaskOut)
def reject_task(
    task_id: int,
    comment: str = Form(""),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.get(models.Task, task_id)
    _assert_reviewer(t, user)
    assert_project_open(db, t.project_id, user)
    if t.status != models.TASK_STATUS_COMPLETED:
        raise HTTPException(status_code=400, detail="只有待确认的任务可以驳回")
    if not comment.strip():
        raise HTTPException(status_code=400, detail="驳回时请填写驳回原因")
    t.status = models.TASK_STATUS_REJECTED
    t.review_comment = comment.strip()
    db.add(
        models.Notification(
            user_id=t.assignee_id,
            type=models.NOTIF_TASK_REJECTED,
            message=f"{user.username} 驳回了你的任务《{t.title}》，原因：{comment.strip()}",
            task_id=t.id,
            from_user_id=user.id,
        )
    )
    db.commit()
    db.refresh(t)
    return TaskOut(**serialize_task(db, t))


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.get(models.TaskAttachment, attachment_id)
    if a is None:
        raise HTTPException(status_code=404, detail="附件不存在")
    t = db.get(models.Task, a.task_id)
    if t is None or not is_project_related(db, t.project_id, user):
        raise HTTPException(status_code=403, detail="无权下载该附件")
    path = UPLOAD_DIR / a.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="附件文件缺失")
    quoted = quote(a.file_name)
    return FileResponse(
        path,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
    )