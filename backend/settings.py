import os

# MySQL connection — used by SQLAlchemy async engine
# Format: user:password@host:port/database
MYSQL_USER = os.getenv("MYSQL_USER", "neuralripper")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "dev")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "neuralripper")

DATABASE_URL = f"{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

DATABASE_POOLSIZE = 10
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_RECYCLE = 3600
DATABASE_DEBUG = os.getenv("DATABASE_DEBUG", "").lower() == "true"

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
