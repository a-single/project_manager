from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user, require_pm_or_admin
from ..database import get_db
from ..helpers import (
    assert_project_open,
    can_manage_project,
    is_project_related,
    serialize_project,
)
from ..schemas import MemberAdd, MemberOut, MessageOut, ProjectCreate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])

_JOINABLE_ROLES = {models.ROLE_DEV, models.ROLE_TESTER, models.ROLE_OPS}


@router.get("", response_model=List[ProjectOut])
def list_projects(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 首页/工作台仅展示未归档项目
    q = (
        db.query(models.Project)
        .filter(models.Project.archived == False)  # noqa: E712
        .order_by(models.Project.id.desc())
    )
    if user.role == models.ROLE_ADMIN:
        projects = q.all()
    elif user.role == models.ROLE_PM:
        projects = (
            q.filter(
                (models.Project.manager_id == user.id)
                | (
                    models.Project.id.in_(
                        db.query(models.ProjectMember.project_id).filter(
                            models.ProjectMember.user_id == user.id
                        )
                    )
                )
            )
            .all()
        )
    else:
        projects = (
            q.filter(
                models.Project.id.in_(
                    db.query(models.ProjectMember.project_id).filter(
                        models.ProjectMember.user_id == user.id
                    )
                )
            )
            .all()
        )
    return [ProjectOut(**serialize_project(db, p)) for p in projects]


@router.get("/archived", response_model=List[ProjectOut])
def list_archived_projects(
    name: Optional[str] = None,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    """归档项目列表：仅项目经理/管理员，可按项目名称筛选"""
    q = (
        db.query(models.Project)
        .filter(models.Project.archived == True)  # noqa: E712
        .order_by(models.Project.id.desc())
    )
    if user.role != models.ROLE_ADMIN:
        q = q.filter(models.Project.manager_id == user.id)
    if name:
        q = q.filter(models.Project.name.like(f"%{name.strip()}%"))
    projects = q.all()
    return [ProjectOut(**serialize_project(db, p)) for p in projects]


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(
    project_id: int,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    """项目归档（关闭）：归档后不可派发任务、所有任务状态锁定、普通成员不可见"""
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    p = db.get(models.Project, project_id)
    if p.archived:
        return ProjectOut(**serialize_project(db, p))
    p.archived = True
    db.commit()
    db.refresh(p)
    return ProjectOut(**serialize_project(db, p))


@router.post("/{project_id}/unarchive", response_model=ProjectOut)
def unarchive_project(
    project_id: int,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    """取消归档（仅项目经理/管理员）"""
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    p = db.get(models.Project, project_id)
    if not p.archived:
        return ProjectOut(**serialize_project(db, p))
    p.archived = False
    db.commit()
    db.refresh(p)
    return ProjectOut(**serialize_project(db, p))


@router.post("", response_model=ProjectOut)
def create_project(
    body: ProjectCreate,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    p = models.Project(name=body.name, description=body.description, manager_id=user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return ProjectOut(**serialize_project(db, p))


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.get(models.Project, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if not is_project_related(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权访问该项目")
    return ProjectOut(**serialize_project(db, p))


@router.delete("/{project_id}", response_model=MessageOut)
def delete_project(
    project_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除项目（仅归档项目，不设置任何前置条件）：管理员或项目负责人可操作，关联数据一并清理。"""
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    p = db.get(models.Project, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    if not p.archived:
        raise HTTPException(status_code=400, detail="请先归档项目后再删除")
    # 级联清理：附件 → 通知 → 任务 → 成员 → 项目
    task_ids = [
        t.id for t in db.query(models.Task.id).filter(models.Task.project_id == project_id).all()
    ]
    if task_ids:
        db.query(models.TaskAttachment).filter(
            models.TaskAttachment.task_id.in_(task_ids)
        ).delete(synchronize_session=False)
        db.query(models.Notification).filter(
            models.Notification.task_id.in_(task_ids)
        ).delete(synchronize_session=False)
        db.query(models.Task).filter(models.Task.project_id == project_id).delete(
            synchronize_session=False
        )
    db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id
    ).delete(synchronize_session=False)
    db.query(models.Project).filter(models.Project.id == project_id).delete(
        synchronize_session=False
    )
    db.commit()
    return MessageOut(message="项目已删除")


@router.get("/{project_id}/members", response_model=List[MemberOut])
def list_members(
    project_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not is_project_related(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权访问该项目")
    rows = (
        db.query(models.ProjectMember, models.User)
        .join(models.User, models.User.id == models.ProjectMember.user_id)
        .filter(models.ProjectMember.project_id == project_id)
        .order_by(models.ProjectMember.id)
        .all()
    )
    return [
        MemberOut(
            id=m.id,
            user_id=u.id,
            username=u.username,
            full_name=u.full_name or "",
            email=u.email or "",
            phone=u.phone or "",
            role=u.role,
            role_label=models.ROLE_LABELS.get(u.role, u.role),
            created_at=m.created_at,
        )
        for m, u in rows
    ]


@router.get("/{project_id}/candidates", response_model=List[MemberOut])
def list_candidates(
    project_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """项目经理可纳入项目的人员：开发/测试/运维，且尚未在该项目中。"""
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    existing = {
        u.user_id for u in db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id)
    }
    users = (
        db.query(models.User)
        .filter(models.User.role.in_(_JOINABLE_ROLES))
        .order_by(models.User.id)
        .all()
    )
    return [
        MemberOut(
            id=0,
            user_id=u.id,
            username=u.username,
            full_name=u.full_name or "",
            email=u.email or "",
            phone=u.phone or "",
            role=u.role,
            role_label=models.ROLE_LABELS.get(u.role, u.role),
            created_at=None,
        )
        for u in users
        if u.id not in existing
    ]


@router.post("/{project_id}/members", response_model=MessageOut)
def add_member(
    project_id: int,
    body: MemberAdd,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    assert_project_open(db, project_id, user)
    member_user = db.get(models.User, body.user_id)
    if member_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if member_user.role not in _JOINABLE_ROLES:
        raise HTTPException(status_code=400, detail="只能纳入开发人员、测试人员、运维人员")
    exists = (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == body.user_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="该用户已在项目中")
    db.add(models.ProjectMember(project_id=project_id, user_id=body.user_id))
    db.commit()
    return MessageOut(message="已加入项目")


@router.delete("/{project_id}/members/{user_id}", response_model=MessageOut)
def remove_member(
    project_id: int,
    user_id: int,
    user: models.User = Depends(require_pm_or_admin),
    db: Session = Depends(get_db),
):
    if not can_manage_project(db, project_id, user):
        raise HTTPException(status_code=403, detail="无权操作该项目")
    assert_project_open(db, project_id, user)
    assigned = (
        db.query(models.Task)
        .filter(
            models.Task.project_id == project_id,
            models.Task.assignee_id == user_id,
            models.Task.status.in_(
                [models.TASK_STATUS_PENDING, models.TASK_STATUS_REJECTED]
            ),
        )
        .count()
    )
    if assigned:
        raise HTTPException(status_code=400, detail="该成员还有未完成任务，无法移出")
    db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_id,
    ).delete()
    db.commit()
    return MessageOut(message="已移出项目")