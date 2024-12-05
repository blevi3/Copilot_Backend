# models/FileHistory.py
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import create_engine

Base = declarative_base()

class FileHistory(Base):
    __tablename__ = 'file_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)

Base.metadata.create_all(bind=engine)