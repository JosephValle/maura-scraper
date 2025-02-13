from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URI

engine = create_engine(DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    published_date = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # New field: stores matched tags as a comma-delimited string.
    content = Column(Text, nullable=True)  # For further content scraping if needed

def init_db():
    """
    Clear the database and then create all tables.
    WARNING: This will drop all existing data each time the server starts.
    """
    Base.metadata.drop_all(bind=engine)   # Clear the DB
    Base.metadata.create_all(bind=engine)   # Re-create tables
