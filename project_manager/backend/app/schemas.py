import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
_PHONE_RE = re.compile(r"^[0-9+\- ]{5,20}$")


def _clean_optional_email(value):
    return value.strip() if isinstance(value, str) else value


def _clean_optional_phone(value):
    return value.strip() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str = ""
    email: str = ""
    phone: str = ""
    role: str
    role_label: str = ""
    created_at: datetime


class TokenResponse(BaseModel):
    token: str
    user: UserOut


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    role: str
    _allowed_roles = ["pm", "dev", "tester", "ops"]

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v):
        if v is None or not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if not v:
            return ""
        v = _clean_optional_email(v)
        if not _EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if not v:
            return ""
        v = _clean_optional_phone(v)
        if not _PHONE_RE.match(v):
            raise ValueError("电话格式不正确")
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    password: Optional[str] = Field(default=None, min_length=1, max_length=64)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    role: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if not v:
            return ""
        v = _clean_optional_email(v)
        if not _EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if not v:
            return ""
        v = _clean_optional_phone(v)
        if not _PHONE_RE.match(v):
            raise ValueError("电话格式不正确")
        return v


class MeUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    password: Optional[str] = Field(default=None, min_length=1, max_length=64)
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v):
        if v is None:
            return v
        if not v.strip():
            raise ValueError("姓名不能为空")
        return v.strip()

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if not v:
            return ""
        v = _clean_optional_email(v)
        if not _EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if not v:
            return ""
        v = _clean_optional_phone(v)
        if not _PHONE_RE.match(v):
            raise ValueError("电话格式不正确")
        return v


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    manager_id: int
    manager_name: str = ""
    created_at: datetime
    archived: bool = False
    member_count: int = 0
    task_count: int = 0
    pending_task_count: int = 0


class MemberAdd(BaseModel):
    user_id: int


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str = ""
    full_name: str = ""
    email: str = ""
    phone: str = ""
    role: str = ""
    role_label: str = ""
    created_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    assignee_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    attachment_required: bool = False
    due_at: Optional[datetime] = None  # 预计完成时间，分钟精度
    is_milestone: bool = False  # 是否里程碑任务

    @field_validator("due_at")
    @classmethod
    def check_due_at_precision(cls, v):
        return v


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    project_name: str = ""
    title: str
    description: str
    assignee_id: int
    assignee_name: str = ""
    assignee_role_label: str = ""
    assigner_id: int
    assigner_name: str = ""
    attachment_required: bool
    status: str
    status_label: str = ""
    comment: str
    review_comment: str = ""
    created_at: datetime
    completed_at: Optional[datetime] = None
    due_at: Optional[datetime] = None  # 预计完成时间
    is_milestone: bool = False  # 是否里程碑任务
    is_overdue: bool = False  # 实时计算的超时标记
    duration_minutes: Optional[int] = None
    attachments: List[dict] = []


class TaskSubmit(BaseModel):
    comment: Optional[str] = None


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    message: str
    task_id: Optional[int]
    from_user_id: Optional[int]
    from_user_name: str = ""
    task_title: str = ""
    is_read: bool
    created_at: datetime


class UnreadCountOut(BaseModel):
    count: int


class StatRecord(BaseModel):
    task_id: int
    title: str
    status: str
    assignee_id: int
    assignee_name: str
    assignee_role_label: str
    project_id: int
    project_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None


class OverdueCount(BaseModel):
    assignee_id: int
    assignee_name: str
    count: int


class MessageOut(BaseModel):
    message: str