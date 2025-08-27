# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URI, KEYWORDS as CONFIG_KEYWORDS  # used only for optional seeding

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
    # Store as ",tag1,tag2," so LIKE '%,tag,%' works reliably.
    tags = Column(String, nullable=True)
    content = Column(Text, nullable=True)

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    # Store lowercased to enforce case-insensitive uniqueness
    value = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('value', name='uq_keywords_value'),
    )

def init_db():
    """
    Create tables if not present. Optionally clear the Articles table on boot.
    Set RESET_DB=1 to drop/recreate Articles only (preserves Keywords).
    """
    Base.metadata.create_all(bind=engine)

    if os.environ.get("RESET_DB") == "1":
        # Drop and recreate only the Articles table (keep Keywords persistent)
        Article.__table__.drop(bind=engine, checkfirst=True)
        Article.__table__.create(bind=engine, checkfirst=True)

    # Optional first-run seed: if there are no keywords, seed from config.
    with SessionLocal() as s:
        existing = s.query(Keyword).limit(1).first()
        if not existing and CONFIG_KEYWORDS:
            to_add = []
            seen = set()
            for k in CONFIG_KEYWORDS:
                if not k:
                    continue
                v = k.strip().lower()
                if v and v not in seen:
                    seen.add(v)
                    to_add.append(Keyword(value=v))
            if to_add:
                s.add_all(to_add)
                s.commit()
