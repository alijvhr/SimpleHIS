from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Drug(Base):
    __tablename__ = "drugs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    manufacturer = Column(String, nullable=False)
    form = Column(String, nullable=False)  # e.g., "قرص", "شربت", "آمپول"
    dosage = Column(String, nullable=False)  # e.g., "500mg", "10ml"
    default_instructions = Column(String, nullable=False)  # e.g., "روزی ۲ عدد بعد غذا"
    price = Column(Numeric(10, 2), nullable=False)
    min_threshold = Column(Integer, default=10)  # Minimum stock threshold
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    stock_transactions = relationship("StockTransaction", back_populates="drug")
    prescription_items = relationship("PrescriptionItem", back_populates="drug")
