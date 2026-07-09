from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum

def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)

class UserRole(str, enum.Enum):
    admin = "admin"
    reception = "reception"
    doctor = "doctor"
    laboratory = "laboratory"
    radiologist = "radiologist"
    pharmacy = "pharmacy"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User", remote_side=[id], foreign_keys=[created_by])
