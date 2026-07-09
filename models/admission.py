from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum

def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)

class AdmissionType(str, enum.Enum):
    doctor = "doctor"
    laboratory = "laboratory"
    radiology = "radiology"

class AdmissionStatus(str, enum.Enum):
    waiting_payment = "waiting_payment"
    paid = "paid"
    completed = "completed"
    cancelled = "cancelled"

class Admission(Base):
    __tablename__ = "admissions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    admission_type = Column(SQLEnum(AdmissionType), nullable=False)
    description = Column(String, nullable=False)  # Reason/complaint
    radiology_type = Column(String, nullable=True)  # e.g., "MRI", "CT Scan"
    status = Column(SQLEnum(AdmissionStatus), default=AdmissionStatus.waiting_payment)
    created_at = Column(DateTime, default=utc_now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="admissions")
    creator = relationship("User", foreign_keys=[created_by])
    payer = relationship("User", foreign_keys=[paid_by])
    radiology_report = relationship("RadiologyReport", back_populates="admission", uselist=False)
    prescription = relationship("Prescription", back_populates="admission", uselist=False)
    lab_orders = relationship("LabOrder", back_populates="admission")
