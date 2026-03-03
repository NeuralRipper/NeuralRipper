DATABASE_URL=""
DATABASE_POOLSIZE = 10  # TCP Connections the sqlalchemy maintainss
DATABASE_MAX_OVERFLOW = 10      # When all connections occupied, new connections allowed to be created
DATABASE_POOL_RECYCLE = 3600    # Recycle connection if timeout
DATABASE_DEBUG = False

GOOGLE_CLIENT_ID = ""  # from Google Cloud Console -> Credentials -> OAuth 2.0 Client ID

JWT_SECRET_KEY = ""    # random secret, e.g. openssl rand -hex 32
JWT_ALGORITHM = "HS256"