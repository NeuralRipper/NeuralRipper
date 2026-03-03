"""
Connection with mysql instance
"""

from sqlalchemy.ext.asyncio import create_async_engine
from settings import DATABASE_DEBUG, DATABASE_URL, DATABASE_POOLSIZE, DATABASE_MAX_OVERFLOW, DATABASE_POOL_RECYCLE

    
def start_engine():
    return create_async_engine(
        f"mysql+aiomysql://{DATABASE_URL}", 
        echo=DATABASE_DEBUG,      
        pool_size=DATABASE_POOLSIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_recycle=DATABASE_POOL_RECYCLE
    )
