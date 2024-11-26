from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Create a base class for models
Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    question = Column(Text)
    answer = Column(Text)

# Database setup (example with SQLite)
DATABASE_URL = "sqlite:///./test.db"  # Update this with your actual database URL
engine = create_engine(DATABASE_URL)

# Create all tables in the database (if they don't exist already)
Base.metadata.create_all(bind=engine)

# Session maker for interacting with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
