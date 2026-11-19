import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = int(os.environ.get("PORT", 3000))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "task_tracker.db"))
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-change-in-production")
TOKEN_EXPIRY_SECONDS = int(os.environ.get("TOKEN_EXPIRY_SECONDS", 86400))  # 24 hours max
LOGIN_MAX_FAILED_ATTEMPTS = int(os.environ.get("LOGIN_MAX_FAILED_ATTEMPTS", 5))
LOGIN_LOCKOUT_SECONDS = int(os.environ.get("LOGIN_LOCKOUT_SECONDS", 300))  # 5 minutes
