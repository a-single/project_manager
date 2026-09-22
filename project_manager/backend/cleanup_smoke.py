"""清理冒烟测试产生的数据（smoke_* 用户及其项目/任务/附件/磁盘文件）。涉及数据库删除。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import models  # noqa: E402
from app.config import UPLOAD_DIR  # noqa: E402
from app.database import SessionLocal  # noqa: E402


def main():
    db = SessionLocal()
    try:
        smoke_user_ids = [
            r[0] for r in db.query(models.User.id).filter(models.User.username.like("smoke_%"))
        ]
        if not smoke_user_ids:
            print("无 smoke_* 测试数据")
            return
        task_ids = [
            r[0]
            for r in db.query(models.Task.id).filter(
                (models.Task.assignee_id.in_(smoke_user_ids))
                | (models.Task.assigner_id.in_(smoke_user_ids))
            )
        ]
        stored_names = [
            r[0]
            for r in db.query(models.TaskAttachment.stored_name).filter(
                models.TaskAttachment.task_id.in_(task_ids)
            )
        ]
        db.query(models.TaskAttachment).filter(
            models.TaskAttachment.task_id.in_(task_ids)
        ).delete(synchronize_session=False)
        db.query(models.Notification).filter(
            (models.Notification.task_id.in_(task_ids))
            | (models.Notification.user_id.in_(smoke_user_ids))
            | (models.Notification.from_user_id.in_(smoke_user_ids))
        ).delete(synchronize_session=False)
        db.query(models.Task).filter(models.Task.id.in_(task_ids)).delete(
            synchronize_session=False
        )
        project_ids = [
            r[0] for r in db.query(models.Project.id).filter(models.Project.manager_id.in_(smoke_user_ids))
        ]
        db.query(models.ProjectMember).filter(
            (models.ProjectMember.project_id.in_(project_ids))
            | (models.ProjectMember.user_id.in_(smoke_user_ids))
        ).delete(synchronize_session=False)
        db.query(models.Project).filter(models.Project.id.in_(project_ids)).delete(
            synchronize_session=False
        )
        db.query(models.User).filter(models.User.id.in_(smoke_user_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        removed_files = 0
        for name in stored_names:
            f = UPLOAD_DIR / name
            if f.exists():
                f.unlink()
                removed_files += 1
        print(
            f"已清理：用户 {len(smoke_user_ids)} 个，项目 {len(project_ids)} 个，"
            f"任务 {len(task_ids)} 个，磁盘附件 {removed_files} 个"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()