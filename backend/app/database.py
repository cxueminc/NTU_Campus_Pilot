from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, create_engine, Time, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL","postgresql://postgres:18U29n02@localhost:5432/ntu_nav")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Facility(Base):
    __tablename__ = "facilities"         # Table name
    __table_args__ = {'schema': 'core'}  # Schema name

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Text, nullable=True)
    name = Column(Text, nullable=False, index=True)
    type = Column(Text, nullable=False, index=True)
    building = Column(Text, nullable=True, index=True)
    floor = Column(Integer, nullable=True)
    attrs = Column(JSONB, nullable=True)  # Using JSONB for better performance
    geom = Column(String, nullable=True)  # USER-DEFINED type, treating as string for now
    open_time = Column(Time, nullable=True)
    close_time = Column(Time, nullable=True)
    open_days = Column(ARRAY(String), nullable=True)
    unit_number = Column(Text, nullable=True)
    map_url = Column(Text, nullable=True)

    class Config:
        from_attributes = True  # For Pydantic v2 compatibility


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()