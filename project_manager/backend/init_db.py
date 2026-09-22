"""数据库初始化脚本：建表 + 创建默认管理员账号 admin/admin。

仅在被明确允许时执行（涉及数据库写操作）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.auth import hash_password  # noqa: E402
from app.config import DATABASE_URL  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app import models  # noqa: E402


def main():
    print(f"连接数据库: {DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    print("数据表创建完成：users / projects / project_members / tasks / task_attachments / notifications")

    db = SessionLocal()
    try:
        admin = db.query(models.User).filter(models.User.role == models.ROLE_ADMIN).first()
        if admin is None:
            db.add(
                models.User(
                    username="admin",
                    password_hash=hash_password("admin"),
                    role=models.ROLE_ADMIN,
                )
            )
            db.commit()
            print("已创建默认管理员账号：admin / admin")
        else:
            print(f"已存在管理员账号：{admin.username}（未修改）")
    finally:
        db.close()


if __name__ == "__main__":
    main()