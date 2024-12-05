# ChatSession.py in models
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    session_id = Column(String, primary_key=True, index=True)
    chat_name = Column(String, nullable=False)

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)

Base.metadata.create_all(bind=engine)
