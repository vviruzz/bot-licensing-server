from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so Alembic metadata includes all tables.
from app.models import *  # noqa: F401,F403,E402
