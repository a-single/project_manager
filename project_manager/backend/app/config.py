import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "your mysql host")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "your mysql user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your mysql password")
DB_NAME = os.getenv("DB_NAME", "your mysql DB_NAME")

DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8"
)

JWT_SECRET = os.getenv("JWT_SECRET", "pj-mger-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# 附件目录
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))
# 附件大小限制
MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB