"""增量数据库迁移脚本：为 tasks 表补充 review_comment 列（任务审核意见/驳回原因）。

幂等：列已存在时跳过。需在征询后执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402

COLUMNS = [
    ("review_comment", "TEXT NULL"),
]


def main():
    with engine.begin() as conn:
        existing = {
            r[0]
            for r in conn.execute(
                text(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'tasks'"
                )
            )
        }
        for name, ddl in COLUMNS:
            if name in existing:
                print(f"列 {name} 已存在，跳过")
            else:
                conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {name} {ddl}"))
                print(f"已添加列 {name}")
        print("任务表迁移完成（review_comment）")


if __name__ == "__main__":
    main()