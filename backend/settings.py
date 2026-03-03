DATABASE_URL=""
DATABASE_POOLSIZE = 10  # TCP Connections the sqlalchemy maintainss
DATABASE_MAX_OVERFLOW = 10      # When all connections occupied, new connections allowed to be created
DATABASE_POOL_RECYCLE = 3600    # Recycle connection if timeout
DATABASE_DEBUG = False          