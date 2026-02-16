from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class RadiologyReport(Base):
    __tablename__ = "radiology_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), unique=True, nullable=False)
    report_text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    admission = relationship("Admission", back_populates="radiology_report")
    creator = relationship("User", foreign_keys=[created_by])
    images = relationship("RadiologyImage", back_populates="report", cascade="all, delete-orphan")

class RadiologyImage(Base):
    __tablename__ = "radiology_images"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("radiology_reports.id"), nullable=False)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("RadiologyReport", back_populates="images")
