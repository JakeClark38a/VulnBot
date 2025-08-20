from contextlib import contextmanager
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from config.config import Configs


def build_db_url():
    """Build database URL with socket support"""
    mysql_config = Configs.db_config.mysql
    
    # Check if socket is specified and exists
    if mysql_config.get('socket') and mysql_config['socket'] != "":
        # Use Unix socket connection
        db_url = f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@/{mysql_config['database']}?unix_socket={mysql_config['socket']}"
    else:
        # Use TCP connection
        db_url = f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
    
    # Add charset if specified
    if mysql_config.get('charset'):
        separator = "&" if "?" in db_url else "?"
        db_url += f"{separator}charset={mysql_config['charset']}"
    
    return db_url


db_url = build_db_url()

# Create engine with additional connection options
engine_kwargs = {}
if Configs.db_config.mysql.get('connect_timeout'):
    engine_kwargs['connect_args'] = {'connect_timeout': Configs.db_config.mysql['connect_timeout']}

if Configs.db_config.mysql.get('pool_size'):
    engine_kwargs['pool_size'] = Configs.db_config.mysql['pool_size']

if Configs.db_config.mysql.get('max_overflow'):
    engine_kwargs['max_overflow'] = Configs.db_config.mysql['max_overflow']

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: DeclarativeMeta = declarative_base()

@contextmanager
def session_scope() -> Session:
    """Context manager for automatic Session acquisition to avoid errors"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with session_scope() as session:
            try:
                result = f(session, *args, **kwargs)
                session.commit()
                return result
            except:
                session.rollback()
                raise

    return wrapper


def create_tables():
    Base.metadata.create_all(bind=engine)
