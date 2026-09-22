from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user, hash_password, require_admin
from ..database import get_db
from ..helpers import ensure_unique_username, serialize_user
from ..schemas import MessageOut, MeUpdate, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

_BUSINESS_ROLES = {models.ROLE_PM, models.ROLE_DEV, models.ROLE_TESTER, models.ROLE_OPS}


@router.get("", response_model=List[UserOut])
def list_users(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员查看全部用户；其他角色查看可用于选择的可加入人员（业务角色）。"""
    q = db.query(models.User).order_by(models.User.id)
    if user.role != models.ROLE_ADMIN:
        q = q.filter(models.User.role.in_(_BUSINESS_ROLES))
    return [UserOut(**serialize_user(u)) for u in q.all()]


@router.post("", response_model=UserOut)
def create_user(
    body: UserCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if body.role not in _BUSINESS_ROLES:
        raise HTTPException(status_code=400, detail="角色不合法")
    ensure_unique_username(db, body.username)
    u = models.User(
        username=body.username,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        email=body.email or "",
        phone=body.phone or "",
        role=body.role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut(**serialize_user(u))


@router.put("/me", response_model=UserOut)
def update_me(
    body: MeUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.username is not None:
        ensure_unique_username(db, body.username, exclude_id=user.id)
        user.username = body.username
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.email is not None:
        user.email = body.email
    if body.phone is not None:
        user.phone = body.phone
    db.commit()
    db.refresh(user)
    return UserOut(**serialize_user(user))


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    u = db.get(models.User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.role is not None:
        if body.role not in _BUSINESS_ROLES:
            raise HTTPException(status_code=400, detail="角色不合法")
        if u.role == models.ROLE_ADMIN:
            raise HTTPException(status_code=400, detail="不能修改管理员角色的账号")
        u.role = body.role
    if body.username is not None:
        ensure_unique_username(db, body.username, exclude_id=user_id)
        u.username = body.username
    if body.password is not None:
        u.password_hash = hash_password(body.password)
    if body.full_name is not None:
        u.full_name = body.full_name
    if body.email is not None:
        u.email = body.email
    if body.phone is not None:
        u.phone = body.phone
    db.commit()
    db.refresh(u)
    return UserOut(**serialize_user(u))


@router.delete("/{user_id}", response_model=MessageOut)
def delete_user(
    user_id: int,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    u = db.get(models.User, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if u.role == models.ROLE_ADMIN:
        raise HTTPException(status_code=400, detail="不能删除管理员账号")
    if db.query(models.Project).filter(models.Project.manager_id == user_id).count():
        raise HTTPException(status_code=400, detail="该用户是项目负责人，无法删除")
    if db.query(models.ProjectMember).filter(models.ProjectMember.user_id == user_id).count():
        raise HTTPException(status_code=400, detail="该用户已被加入项目，无法删除，请先从项目中移除")
    if db.query(models.Task).filter(
        (models.Task.assignee_id == user_id) | (models.Task.assigner_id == user_id)
    ).count():
        raise HTTPException(status_code=400, detail="该用户有关联的任务，无法删除")
    if db.query(models.TaskAttachment).filter(models.TaskAttachment.uploader_id == user_id).count():
        raise HTTPException(status_code=400, detail="该用户有上传的附件，无法删除")
    db.query(models.Notification).filter(models.Notification.user_id == user_id).delete()
    db.delete(u)
    db.commit()
    return MessageOut(message="用户已删除")