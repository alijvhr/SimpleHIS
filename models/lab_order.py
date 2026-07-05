from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone
import enum


def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)


class LabOrderStatus(str, enum.Enum):
    waiting_payment = "waiting_payment"
    paid = "paid"
    collected = "collected"
    resulted = "resulted"
    cancelled = "cancelled"


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(SQLEnum(LabOrderStatus), default=LabOrderStatus.waiting_payment)
    clinical_note = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="lab_orders")
    admission = relationship("Admission", back_populates="lab_orders")
    creator = relationship("User", foreign_keys=[created_by])
    payer = relationship("User", foreign_keys=[paid_by])
    items = relationship("LabOrderItem", back_populates="order", cascade="all, delete-orphan")


class LabOrderItem(Base):
    __tablename__ = "lab_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("lab_orders.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("lab_tests.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    notes = Column(String, nullable=True)

    order = relationship("LabOrder", back_populates="items")
    test = relationship("LabTest", back_populates="order_items")
    result = relationship("LabResult", back_populates="order_item", uselist=False, cascade="all, delete-orphan")
