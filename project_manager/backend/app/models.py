from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base

ROLE_ADMIN = "admin"
ROLE_PM = "pm"
ROLE_DEV = "dev" 
ROLE_TESTER = "tester"
ROLE_OPS = "ops"
ROLES = [ROLE_ADMIN, ROLE_PM, ROLE_DEV, ROLE_TESTER, ROLE_OPS]
ROLE_LABELS = {
    ROLE_ADMIN: "管理员",
    ROLE_PM: "项目经理",
    ROLE_DEV: "开发人员",
    ROLE_TESTER: "测试人员",
    ROLE_OPS: "运维人员",
}

TASK_STATUS_PENDING = "pending"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_APPROVED = "approved"
TASK_STATUS_REJECTED = "rejected"
TASK_STATUS_OVERDUE = "overdue"  # 展示态（实时计算，不落库）
TASK_STATUS_LATE = "late"  # 展示态：已确认但超时完成（已延毕，不落库）
TASK_STATUS_LABELS = {
    TASK_STATUS_PENDING: "待处理",
    TASK_STATUS_COMPLETED: "待确认",
    TASK_STATUS_APPROVED: "已确认",
    TASK_STATUS_REJECTED: "已驳回",
    TASK_STATUS_OVERDUE: "已超时",
    TASK_STATUS_LATE: "已延毕",
}

NOTIF_TASK_ASSIGNED = "task_assigned"
NOTIF_TASK_COMPLETED = "task_completed"
NOTIF_TASK_APPROVED = "task_approved"
NOTIF_TASK_REJECTED = "task_rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(50), nullable=False, default="")
    email = Column(String(100), nullable=False, default="")
    phone = Column(String(30), nullable=False, default="")
    role = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    archived = Column(Boolean, default=False, nullable=False, index=True)

    manager = relationship("User", foreign_keys=[manager_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    project = relationship("Project", back_populates="members")
    user = relationship("User")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    attachment_required = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default=TASK_STATUS_PENDING, nullable=False, index=True)
    comment = Column(Text, default="")
    review_comment = Column(Text, default="")
    due_at = Column(DateTime, nullable=True, index=True)  # 预计完成时间
    is_milestone = Column(Boolean, default=False, nullable=False)  # 是否里程碑任务
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True, index=True)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    assigner = relationship("User", foreign_keys=[assigner_id])
    attachments = relationship(
        "TaskAttachment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskAttachment.uploaded_at",
    )


class TaskAttachment(Base):
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now, nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)
    message = Column(String(500), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id])
    task = relationship("Task")
    from_user = relationship("User", foreign_keys=[from_user_id])