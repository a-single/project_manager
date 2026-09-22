from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, notifications, projects, report, stats, tasks, users

app = FastAPI(title="运维项目管理工作平台 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(report.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}