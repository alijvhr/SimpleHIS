from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum

def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)

class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    national_id = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    gender = Column(SQLEnum(Gender), nullable=False)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    admissions = relationship("Admission", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    lab_orders = relationship("LabOrder", back_populates="patient")
