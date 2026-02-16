from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # Positive for addition, negative for subtraction
    reason = Column(String, nullable=False)  # e.g., "خرید اولیه", "موجودی اضافه", "تحویل نسخه"
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    drug = relationship("Drug", back_populates="stock_transactions")
    creator = relationship("User", foreign_keys=[created_by])
