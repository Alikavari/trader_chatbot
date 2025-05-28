from sqlalchemy import create_engine, MetaData
from trader_chatbot.main import metadata, DATABASE_URL

engine = create_engine(DATABASE_URL)


def create_tables():
    metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
    print("Tables created successfully.")
