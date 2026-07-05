from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum

def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)

class PayableType(str, enum.Enum):
    admission = "admission"
    prescription = "prescription"
    lab_order = "lab_order"

class PaymentStatus(str, enum.Enum):
    paid = "paid"
    cancelled = "cancelled"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payable_type = Column(SQLEnum(PayableType), nullable=False)
    payable_id = Column(Integer, nullable=False)  # FK to Admission.id or Prescription.id
    amount = Column(Numeric(10, 2), nullable=False)
    receipt_number = Column(String, nullable=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.paid)
    created_at = Column(DateTime, default=utc_now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
