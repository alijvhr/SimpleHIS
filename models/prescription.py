from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class PrescriptionStatus(str, enum.Enum):
    waiting_payment = "waiting_payment"
    paid = "paid"
    dispensed = "dispensed"
    cancelled = "cancelled"

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=True)  # null for manual
    is_manual = Column(Boolean, default=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(PrescriptionStatus), default=PrescriptionStatus.waiting_payment)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    dispensed_at = Column(DateTime, nullable=True)
    dispensed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    admission = relationship("Admission", back_populates="prescription")
    creator = relationship("User", foreign_keys=[created_by])
    dispenser = relationship("User", foreign_keys=[dispensed_by])
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    instructions = Column(String, nullable=False)  # Default from Drug, but editable
    
    # Relationships
    prescription = relationship("Prescription", back_populates="items")
    drug = relationship("Drug", back_populates="prescription_items")
