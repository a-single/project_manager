"""增量数据库迁移脚本：为 users 表补充 姓名/邮箱/电话 列并初始化已有管理员姓名。

幂等：列已存在时跳过。需在征询后执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402

from app.config import DATABASE_URL  # noqa: E402
from app.database import engine  # noqa: E402

COLUMNS = [
    ("full_name", "VARCHAR(50) NOT NULL DEFAULT ''"),
    ("email", "VARCHAR(100) NOT NULL DEFAULT ''"),
    ("phone", "VARCHAR(30) NOT NULL DEFAULT ''"),
]


def main():
    with engine.begin() as conn:
        existing = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'"
                )
            )
        }
        for name, ddl in COLUMNS:
            if name in existing:
                print(f"列 {name} 已存在，跳过")
            else:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                print(f"已添加列 {name}")
        # 管理员补默认姓名
        conn.execute(
            text(
                "UPDATE users SET full_name = '管理员' "
                "WHERE role = 'admin' AND (full_name IS NULL OR full_name = '')"
            )
        )
        print("迁移完成（admin 姓名已初始化）")


if __name__ == "__main__":
    main()