from sqlalchemy import Column, Integer, String, Numeric, Boolean
from sqlalchemy.orm import relationship
from database import Base


class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    sample_type = Column(String, nullable=True)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    male_normal_range = Column(String, nullable=True)
    female_normal_range = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    order_items = relationship("LabOrderItem", back_populates="test")
