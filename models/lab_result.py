from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("lab_order_items.id"), unique=True, nullable=False)
    value = Column(String, nullable=False)
    flag = Column(String, nullable=True)
    entered_at = Column(DateTime, default=utc_now)
    entered_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    order_item = relationship("LabOrderItem", back_populates="result")
    creator = relationship("User", foreign_keys=[entered_by])
