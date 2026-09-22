"""端到端 API 冒烟测试：覆盖完整业务流程。

前置：后端已在 127.0.0.1:8000 运行，数据库已初始化（含 admin/admin）。
使用测试用户名：smoke_pm1 / smoke_dev1 / smoke_tester1 / smoke_ops1 / smoke_admin1
"""
import sys

import requests

BASE = "http://127.0.0.1:8000/api"

passed = 0
failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {extra}")


class Worker:
    def __init__(self):
        self.token = None

    def req(self, method, path, **kw):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        r = requests.request(method, BASE + path, headers=headers, timeout=15, **kw)
        try:
            body = r.json() if r.content else {}
        except Exception:
            body = r.text
        return r.status_code, body


def login(username, password):
    w = Worker()
    code, body = w.req("POST", "/auth/login", json={"username": username, "password": password})
    return w, code, body


def main():
    print("== 0 健康检查 ==")
    code, body = Worker().req("GET", "/health")
    check("health", code == 200, body)

    print("== 1 登录与未授权 ==")
    w, code, body = login("admin", "admin")
    check("admin/admin 登录成功", code == 200 and body.get("token"), body)
    w.token = body["token"]

    code, _ = Worker().req("GET", "/users")
    check("未登录访问被拒(401)", code == 401, code)

    print("== 2 管理员创建用户 ==")
    for name, role in [("smoke_pm1", "pm"), ("smoke_dev1", "dev"),
                       ("smoke_tester1", "tester"), ("smoke_ops1", "ops")]:
        if login(name, "smoke123")[1] == 200:  # 已存在则跳过创建
            check(f"{name} 已存在", True)
            continue
        code, body = w.req("POST", "/users", json={"username": name, "password": "smoke123", "full_name": f"测试{role}", "role": role})
        check(f"创建 {name}({role})", code == 200, body)

    code, body = w.req("POST", "/users", json={"username": "smoke_bad", "password": "x", "full_name": "x", "role": "admin"})
    check("不能创建 admin 角色", code == 400, body)
    code, body = w.req("POST", "/users", json={"username": "smoke_bad2", "password": "x", "full_name": "x", "role": "hacker"})
    check("非法角色被拒", code == 400, body)
    code, body = w.req("POST", "/users", json={"username": "smoke_bad3", "password": "x", "full_name": "", "role": "dev"})
    check("姓名为空被拒", code == 422, body)
    code, body = w.req("POST", "/users", json={"username": "smoke_bad4", "password": "x", "full_name": "x", "email": "not-an-email", "role": "dev"})
    check("邮箱格式非法被拒", code == 422, body)

    print("== 3 PM 登录与项目 ==")
    pm, code, body = login("smoke_pm1", "smoke123")
    check("pm 登录", code == 200)
    pm.token = body["token"]

    code, body = pm.req("POST", "/projects", json={"name": "冒烟测试项目", "description": "e2e"})
    check("pm 创建项目", code == 200, body)
    project_id = body.get("id")
    check("项目负责人为 pm", body.get("manager_name") == "smoke_pm1", body)
    if not project_id:
        print("  项目创建失败，终止"); sys.exit(1)

    print("== 4 添加成员（只允许 dev/tester/ops） ==")
    for uname in ("smoke_dev1", "smoke_tester1", "smoke_ops1"):
        _, users_body = pm.req("GET", "/users")
        uid = next(u["id"] for u in users_body if u["username"] == uname)
        code, body = pm.req("POST", f"/projects/{project_id}/members", json={"user_id": uid})
        check(f"添加成员 {uname}", code == 200, body)
    _, cand_body = pm.req("GET", f"/projects/{project_id}/candidates")
    check("候选列表中不再包含已加入成员", all(c["username"] != "smoke_dev1" for c in cand_body), cand_body)

    _, users_body = pm.req("GET", "/users")
    fake_id = next(u["id"] for u in users_body if u["username"] == "smoke_pm1")
    code, body = pm.req("POST", f"/projects/{project_id}/members", json={"user_id": fake_id})
    check("不能把项目经理加入成员", code == 400, body)

    print("== 5 派发任务与通知 ==")
    _, users_body = pm.req("GET", "/users")
    dev_id = next(u["id"] for u in users_body if u["username"] == "smoke_dev1")
    code, body = pm.req("POST", f"/projects/{project_id}/tasks",
                        json={"assignee_id": dev_id, "title": "开发首页接口(需附件)",
                              "description": "按接口规范实现", "attachment_required": True})
    check("派发任务(要求附件)", code == 200 and body.get("status") == "pending", body)
    task_id = body.get("id")

    code, body = pm.req("POST", f"/projects/{project_id}/tasks",
                        json={"assignee_id": dev_id, "title": "编写测试用例", "description": ""})
    check("派发任务(无附件要求)", code == 200, body)
    task_id2 = body["id"]
    check("attachment_required 默认 false", body.get("attachment_required") is False, body)

    dev, code, body = login("smoke_dev1", "smoke123")
    dev.token = body["token"]
    _, notif = dev.req("GET", "/notifications/unread-count")
    check("dev 收到未读通知", notif.get("count", 0) >= 2, notif)
    _, me_tasks = dev.req("GET", "/tasks", params={"scope": "mine"})
    check("dev 我的任务含 2 条", len(me_tasks) >= 2, me_tasks)

    print("== 6 完成工作：附件/留言规则 ==")
    code, body = dev.req("POST", f"/tasks/{task_id}/complete")
    check("无附件且无留言被拒(400)", code == 400, body)

    code, body = dev.req("POST", f"/tasks/{task_id}/complete", data={"comment": "已完成，附optiot如下"})
    check("有留言完成成功", code == 200 and body.get("status") == "completed", body)
    check("完成时间已记录", bool(body.get("completed_at")), body)

    # 第二个任务：带附件完成
    files = {"files": ("报告.docx", b"fake-doc-content-e2e", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    code, body = dev.req("POST", f"/tasks/{task_id2}/complete", data={"comment": "完成了"}, files=files)
    check("带附件完成成功", code == 200, body)
    check("附件已记录", len(body.get("attachments", [])) == 1, body)
    code, body = dev.req("POST", f"/tasks/{task_id2}/complete")
    check("重复完成被拒(400)", code == 400, body)

    print("== 6.5 项目经理确认/驳回流转 ==")
    code, body = pm.req("POST", f"/tasks/{task_id}/reject")
    check("驳回无原因被拒(400)", code == 400, body)
    code, body = pm.req("POST", f"/tasks/{task_id}/reject", data={"comment": "接口实现不符合规范"})
    check("驳回成功", code == 200 and body.get("status") == "rejected", body)
    check("驳回原因已记录", body.get("review_comment") == "接口实现不符合规范", body)
    _, n_items = dev.req("GET", "/notifications", params={"unread_only": True})
    check("dev 收到驳回通知", any(n["type"] == "task_rejected" for n in n_items), n_items)
    code, body = dev.req("POST", f"/tasks/{task_id}/approve")
    check("工作人员不能确认任务(403)", code == 403, body)

    code, body = dev.req("POST", f"/tasks/{task_id}/complete", data={"comment": "已按规范重新实现"})
    check("驳回后重新提交成功", code == 200 and body.get("status") == "completed", body)

    code, body = pm.req("POST", f"/tasks/{task_id}/approve")
    check("项目经理确认完成", code == 200 and body.get("status") == "approved", body)
    code, body = pm.req("POST", f"/tasks/{task_id}/approve")
    check("已完成任务不能重复确认", code == 400, body)
    _, n_items = pm.req("GET", "/notifications", params={"unread_only": True})
    check("PM 收到完成通知(含task_id2与重提)", sum(1 for n in n_items if n["type"] == "task_completed") >= 2, n_items)

    print("== 7 项目经理收到完成通知 ==")
    _, notif = pm.req("GET", "/notifications/unread-count")
    check("pm 收到完成通知", notif.get("count", 0) >= 2, notif)
    _, items = pm.req("GET", "/notifications")
    check("通知列表含完成类型", any(n["type"] == "task_completed" for n in items), items)

    print("== 8 附件下载 ==")
    _, items = dev.req("GET", "/tasks", params={"scope": "mine"})
    att = next(a for t in items if t["id"] == task_id2 for a in t["attachments"])
    r = requests.get(f"http://127.0.0.1:8000/api/attachments/{att['id']}/download",
                     headers={"Authorization": f"Bearer {dev.token}"}, timeout=15)
    check("附件可下载", r.status_code == 200 and r.content == b"fake-doc-content-e2e", r.status_code)

    print("== 8.5 个人资料修改（普通用户自行修改姓名/邮箱/电话） ==")
    code, body = dev.req("PUT", "/users/me", json={"full_name": "修改后的名字", "email": "dev1@example.com", "phone": "13800000000"})
    check("dev 修改自己姓名/邮箱/电话", code == 200 and body.get("full_name") == "修改后的名字", body)
    code, body = dev.req("PUT", "/users/me", json={"full_name": ""})
    check("修改时姓名为空被拒", code == 422, body)
    code, body = dev.req("PUT", "/users/me", json={"email": "bad-email"})
    check("修改时邮箱非法被拒", code == 422, body)
    code, body = dev.req("PUT", "/users/me", json={"phone": "123"})
    check("修改时电话非法被拒", code == 422, body)

    print("== 9 任务统计 ==")
    today = __import__("datetime").date.today().isoformat()
    code, body = pm.req("GET", "/stats/task-records",
                        params={"project_id": project_id, "start": "2020-01-01", "end": today})
    check("统计返回完成记录2条", code == 200 and len(body) == 2, body)
    check("统计含耗时", all(r.get("duration_minutes") is not None for r in body), body)
    code, body = pm.req("GET", "/stats/task-records",
                        params={"project_id": project_id, "start": "2020-01-01", "end": today, "user_id": dev_id})
    check("按人员过滤统计", code == 200 and all(r["assignee_name"] == "smoke_dev1" for r in body), body)
    code, body = pm.req("GET", "/stats/task-records",
                        params={"project_id": project_id, "start": "2020-01-01", "end": "2019-01-01"})
    check("起止时间倒置被拒", code == 400)

    print("== 10 日报导出 ==")
    code, body = dev.req("GET", "/report/mine",
                         params={"start": "2020-01-01", "end": today})
    check("dev 日报记录", code == 200 and len(body) >= 2, body)

    print("== 11 权限校验 ==")
    code, body = dev.req("POST", "/projects", json={"name": "x"})
    check("dev 不能创建项目", code == 403, code)
    code, body = dev.req("GET", "/users")
    check("dev 拿到的用户列表仅业务角色", code == 200 and all(u["role"] != "admin" for u in body), body)
    code, body = dev.req("GET", "/projects/{}/members".format(project_id))
    check("dev 可查看所属项目成员", code == 200)
    _, other_tasks = dev.req("GET", "/tasks", params={"scope": "managed"})
    check("dev 无项目管理任务", len(other_tasks) == 0, other_tasks)

    code, body = dev.req("POST", "/projects/{}/tasks".format(project_id),
                         json={"assignee_id": dev_id, "title": "x"})
    check("dev 不能派发任务", code == 403, code)

    print("== 12 删除保护 ==")
    code, body = w.req("DELETE", f"/users/{dev_id}")
    check("有任务用户不可删除", code == 400, body)
    code, body = w.req("DELETE", f"/projects/{project_id}")
    check("有任务项目不可删除", code == 400, body)

    print(f"\n结果：通过 {passed} 项，失败 {failed} 项")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()