"""验证工作人员账号(密码123456)在移动端的数据可见性（测试后删除）"""
import requests

BASE = "http://localhost:5174/api"
results = []


def check(name, cond, info=""):
    results.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name, ("| " + str(info)) if info else "")


users = requests.get(f"{BASE}/users")
# 需要管理员取用户，直接先登录 admin 拿列表
sadmin = requests.Session()
r = sadmin.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin"})
sadmin.headers["Authorization"] = f"Bearer {r.json()['token']}"
users = sadmin.get(f"{BASE}/users").json()
emps = [u for u in users if u["role"] in ("dev", "tester", "ops")]
print("工作人员账号:", [(u["username"], u["role"], u["full_name"]) for u in emps])

for u in emps[:6]:
    e = requests.Session()
    r = e.post(f"{BASE}/auth/login", json={"username": u["username"], "password": "123456"})
    if r.status_code != 200:
        check(f"{u['username']} 登录", False, r.text[:80])
        continue
    e.headers["Authorization"] = f"Bearer {r.json()['token']}"
    proj = e.get(f"{BASE}/projects")
    tasks = e.get(f"{BASE}/tasks", params={"scope": "mine"})
    names = [p["name"] for p in proj.json()] if proj.ok else ["ERR"]
    check(f"{u['username']}({u['full_name']}) 登录+项目", proj.ok, f"可见项目={names} 任务={len(tasks.json()) if tasks.ok else 'ERR'}")

print(f"\n结果: {sum(1 for _,c in results if c)}/{len(results)} 通过")