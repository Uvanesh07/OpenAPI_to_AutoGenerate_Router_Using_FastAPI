import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# Create an asynchronous engine for MySQL
engine = create_async_engine(
    DATABASE_URL,
    echo=True,             # Log SQL queries for debugging
    pool_size=10,         # Adjust pool size according to your needs
    max_overflow=20,      # Allow overflow connections if pool is full
    pool_timeout=60,      # Increase timeout before failing (in seconds)
    pool_recycle=1800     # Recycle connections after 30 minutes (optional)
)

# Create a sessionmaker bound to the engine
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class ConnectionManager:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        if self.session is None:
            self.session = AsyncSessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.session:
            await self.session.close()
            self.session = None
