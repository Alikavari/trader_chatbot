from sqlmodel import create_engine, SQLModel, Session
from contextlib import asynccontextmanager

DATABASE_URL = "sqlite:///wallet.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app):
    create_db_and_tables()
    yield
