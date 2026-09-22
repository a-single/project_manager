# 运维项目管理工作平台
一个面向运维/研发团队的轻量级项目管理平台，提供项目、任务、成员、里程碑、统计、消息通知与日报导出等能力。

# 支持三种访问方式：
PC 端 Web（Vue3 + Element Plus）
手机端 Web（Vue3 移动适配，独立页面）
Android APK（WebView 壳 + JSBridge）

# 技术栈
后端	FastAPI + SQLAlchemy + PyMySQL + PyJWT（Python 3）
前端	Vue3 + Vite + Element Plus + Pinia + ECharts + Axios
数据库	MySQL 5.7+
移动端	Android 原生 WebView 壳（Java），嵌手机端 Web 页面
# 功能特性
## 用户与角色
角色：管理员 / 项目经理 / 开发人员 / 测试人员 / 运维人员
管理员可创建用户，维护用户名、姓名、邮箱、电话与角色
## 项目管理
创建项目、指定项目负责人（项目经理）
向项目添加/移除成员（可查看成员邮箱、电话）
项目成员列表支持权限划分：普通成员仅可查看，不可增删
项目关闭（归档）：归档后所有任务/成员写操作被锁定、仅可查看
归档项目支持恢复；归档项目支持永久删除（无条件，级联清理任务/成员/统计/通知等关联数据），未归档项目不可删除
## 任务管理
项目经理/管理员向项目成员派发任务
可设置任务的预计完成时间（分钟级）与是否里程碑任务
任务可要求提交附件产物（多文件，单文件 ≤ 20MB）
任务流转：待处理 → 提交完成(待确认) → 确认完成 / 驳回重做
超时判定（实时计算）：未完成且超过预计完成时间显示「已超时」
延毕判定（实时计算）：确认完成但实际完成时间晚于预计完成时间，状态显示「已延毕」，且仍计入“人员超时任务数量”统计
任务列表支持按预计完成时间从近到远排序、状态筛选、分页（每页 5/10/20 条），列表内独立滚动，页面本身不出现滚动条
任务面板支持导出当前筛选结果为 CSV（仅经理/管理员可见）
# 图片展示
## 项目经理工作台
首页展示：待确认任务 / 未完成任务 / 已超时任务 / 项目里程碑
<img width="1912" height="922" alt="首页" src="https://github.com/user-attachments/assets/c49bb60b-d3f4-4ecb-adcb-e6039766b96e" />

## 项目任务面板：全部 / 我的 视角切换，状态筛选
<img width="1912" height="922" alt="任务明细" src="https://github.com/user-attachments/assets/61dc0349-d7bf-466f-9bb4-9240cdac3ff6" />

## 统计与报表
甘特图（任务时间跨度）
三种条形图：任务数量 / 人员工作时长（不足 0.1 小时按 0.1 计）/ 人员超时任务数量
支持按项目、日期范围、人员筛选
<img width="1912" height="2022" alt="任务统计" src="https://github.com/user-attachments/assets/921ca285-f5ce-4c87-b3c8-988d13c1a8c3" />

## 日报导出 CSV（记录归属）
<img width="1912" height="922" alt="日报导出" src="https://github.com/user-attachments/assets/24058e15-d519-410c-bddb-cb658f67cd56" />

## 消息通知
任务派发、提交、确认、驳回均产生站内通知
未读数量角标、一键已读；手机端有新任务可声音提醒
<img width="482" height="476" alt="消息提醒" src="https://github.com/user-attachments/assets/b4b5c2f0-26f5-4e70-98c5-4dde68b112ce" />

## 移动端
登录页/设置：手机端登录前即可通过左上角齿轮设置服务器地址
手机端成员信息支持点击复制手机号 / 邮箱
<img width="1440" height="3200" alt="微信图片_20260922144524_108_46" src="https://github.com/user-attachments/assets/3f190e6a-cf5a-4d8b-bf49-4d6546653442" /><img width="1280" height="2844" alt="微信图片_20260922144525_109_46" src="https://github.com/user-attachments/assets/c15f803c-ccf4-470d-a4d7-663a77db16c8" /><img width="1280" height="6316" alt="微信图片_20260922144526_110_46" src="https://github.com/user-attachments/assets/daaf9326-3aee-4de2-8321-a823a7b1541b" />

## 快速开始
默认账号
角色	用户名	密码
管理员	admin	admin
管理员账号由 init_db.py 自动创建；项目经理与工作人员由管理员在“用户管理”中创建。首次使用建议登录后修改各处隐私信息。

## 典型流程
1、管理员创建工作人员账号；
2、项目经理新建项目，并在项目内添加成员；
3、项目经理向成员派发任务（可设置预计完成时间/里程碑/附件要求）；
4、成员完成工作并提交（可上传附件、填写留言）；
5、项目经理确认完成或驳回；驳回后成员可重新提交；
6、超时延毕的任务在确认后显示「已延毕」；
7、通过“任务统计”查看甘特图与条形图，导出日报/任务 CSV；
8、项目结项后由项目经理“关闭项目”归档，必要时可恢复或永久删除。

# 部署方式
## 0. 准备
Python 3.10+，Node.js 16+，MySQL 5.7+（建议 utf8mb4）
## 创建数据库：
sql
CREATE DATABASE 数据库名 DEFAULT CHARACTER SET utf8mb4;
## 1. 配置后端
复制/编辑 backend/.env，按环境修改：
env
DB_HOST=你的数据库IP
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=数据库名
JWT_SECRET=生产环境请更换为随机长字符串
创建虚拟环境并安装依赖：
bash
cd backend
python -m venv venv
### Windows
venv\Scripts\activate
### Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
### Windows：
venv\Scripts\python.exe -m pip install -r backend\requirements.txt
## 2. 初始化数据库
建表 + 默认管理员：
venv\Scripts\python.exe backend\init_db.py
## 增量迁移（见 数据库迁移）：
venv\Scripts\python.exe backend\migrate_tasks.py
## 3. 启动后端服务
venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
开发热重载可加 --reload。
验证：浏览器访问 http://<服务器IP>:8000/api/health 返回 {"status":"ok"}。

## 4. 启动 PC 端前端
bash
cd frontend
npm install
npm run dev        # 开发：端口 5173，/api 代理到 127.0.0.1:8000
npm run build      # 打包：产物在 dist/，可用 npm run preview 预览
生产建议：用 Nginx 将 dist 托管，并将 /api 反向代理到后端 8000 端口。

## 5. 启动手机端前端
bash
cd mobile
npm install
npm run dev        # 开发：端口 5174，/api 代理到 127.0.0.1:8000
npm run build      # 打包：产物在 dist/
手机 App 配置服务器地址为 <服务器IP>:5174 即可使用。

# 数据库迁移
模型变更（如 tasks.due_at / is_milestone、projects.archived 等）不在 init_db 自动建表内，需手工执行以下增量 SQL（幂等，可重复执行）：

ALTER TABLE tasks ADD COLUMN due_at DATETIME NULL;
ALTER TABLE tasks ADD COLUMN is_milestone TINYINT(1) NOT NULL DEFAULT 0;
ALTER TABLE projects ADD COLUMN archived TINYINT(1) NOT NULL DEFAULT 0;
并执行：
venv\Scripts\python.exe backend\migrate_tasks.py

# 注意事项
归档项目删除为永久操作（级联删除任务/成员/通知），操作前有确认提示。
超时/延毕均为实时计算展示态，不写入数据库，由系统时间与预计完成时间判定，不可手工修改。
JWT 默认 24 小时过期，生产环境请更换 JWT_SECRET。
后端跨域已放开（*），如有内网安全要求建议收紧密集。
手机端 Web 与 APK 共用后端地址。

# License
本项目未指定开源许可证，随意商用将承担法律责任。

# 支持与联系
<img width="1279" height="1743" alt="微信图片_20260922180958_111_46" src="https://github.com/user-attachments/assets/f78c4e7e-8019-47f7-a197-5cec783e84c5" />
邮箱：sir@zknu.cn
