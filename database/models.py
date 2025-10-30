"""
SQLAlchemy models for the vulnerability alert system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Vulnerability(Base):
    """Model for storing vulnerability information"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(50), unique=True, index=True, nullable=False)  # CVE or other unique identifier
    product_name = Column(String(200), nullable=False, index=True)
    product_version = Column(String(100), nullable=True)
    oem_name = Column(String(100), nullable=False, index=True)
    severity_level = Column(String(20), nullable=False, index=True)  # Critical, High, Medium, Low
    vulnerability_description = Column(Text, nullable=False)
    mitigation_strategy = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=False, index=True)
    discovered_date = Column(DateTime, default=func.now(), nullable=False)
    source_url = Column(String(500), nullable=True)
    cvss_score = Column(String(10), nullable=True)
    affected_versions = Column(Text, nullable=True)  # JSON string of affected versions
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="vulnerability")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_oem_severity', 'oem_name', 'severity_level'),
        Index('idx_published_date', 'published_date'),
        Index('idx_product_oem', 'product_name', 'oem_name'),
    )

class Subscription(Base):
    """Model for user email subscriptions"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    oem_name = Column(String(100), nullable=True, index=True)  # None means all OEMs
    product_name = Column(String(200), nullable=True, index=True)  # None means all products
    severity_filter = Column(String(20), nullable=False, default="Critical,High")  # Comma-separated
    is_active = Column(Boolean, default=True, nullable=False)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    last_notified = Column(DateTime, nullable=True)
    
    # Foreign key to vulnerability (for tracking which vulnerabilities triggered notifications)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=True)
    vulnerability = relationship("Vulnerability", back_populates="subscriptions")
    
    # Indexes
    __table_args__ = (
        Index('idx_email_active', 'email', 'is_active'),
        Index('idx_oem_product', 'oem_name', 'product_name'),
    )

class ScanLog(Base):
    """Model for tracking scraping operations"""
    __tablename__ = "scan_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    oem_name = Column(String(100), nullable=False, index=True)
    scan_type = Column(String(20), nullable=False)  # 'scheduled', 'manual', 'error'
    status = Column(String(20), nullable=False)  # 'success', 'error', 'partial'
    vulnerabilities_found = Column(Integer, default=0, nullable=False)
    new_vulnerabilities = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    scan_duration = Column(Integer, nullable=True)  # Duration in seconds
    scan_date = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_oem_scan_date', 'oem_name', 'scan_date'),
        Index('idx_scan_status', 'status', 'scan_date'),
    )

class NotificationLog(Base):
    """Model for tracking sent email notifications"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=False)
    email_sent = Column(Boolean, default=True, nullable=False)
    sent_date = Column(DateTime, default=func.now(), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    subscription = relationship("Subscription")
    vulnerability = relationship("Vulnerability")
    
    # Indexes
    __table_args__ = (
        Index('idx_sent_date', 'sent_date'),
        Index('idx_subscription_vuln', 'subscription_id', 'vulnerability_id'),
    )
