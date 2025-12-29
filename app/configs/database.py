from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
#from contextlib import contextmanager

from app.configs.settings import settings

DATABASE_TYPE = settings.db.database_type

if settings.db.database_url:
    connection_url = settings.db.database_url
else:
    # Default to PostgreSQL
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=settings.db.postgres_user,
        password=settings.db.postgres_password,
        host=settings.db.postgres_host,
        port=settings.db.postgres_port,
        database=settings.db.postgres_db
    )

# Create engine with connection pooling
engine = create_engine(
    connection_url,
    pool_size = 5,
    max_overflow = 10,
    pool_pre_ping = True,  # Test connections for liveness
    echo = True  # Show SQL in logs (debug)
)


# Create session factory (2.0 style)
DBSession = sessionmaker(
    bind = engine,
    autoflush = False,
    expire_on_commit = False,
    future = True  # Enables 2.0 style
)

def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

"""
# Usage of Session
@contextmanager
def get_session()-> Generator[Session, None, None]:
    #Yield a session with automatic cleanup
    session = DBSession()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
"""

class Base(DeclarativeBase):
    pass

# ---- Create Database and Tables if not exists ----
#Base.metadata.create_all(bind = engine)