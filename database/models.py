"""
SQLAlchemy models for the vulnerability alert system
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Organization(Base):
    """Model for tenant/organization"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    enabled_oems = Column(String(500), default="ALL", nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    users = relationship("User", back_populates="organization", foreign_keys="User.organization_id")

class User(Base):
    """Model for system users (analysts/admins)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default="Analyst", nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])

class Invitation(Base):
    """Model for pending organization invitations"""
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    role = Column(String(20), default="Analyst", nullable=False)
    token = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default="Pending")
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Vulnerability(Base):
    """Model for storing vulnerability data"""
    __tablename__ = "vulnerabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    unique_id = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200), nullable=False, index=True)
    product_version = Column(String(100), nullable=True)
    oem_name = Column(String(100), nullable=False, index=True)
    severity_level = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default="Open", nullable=False, index=True)
    vulnerability_description = Column(Text, nullable=False)
    mitigation_strategy = Column(Text, nullable=True)
    published_date = Column(DateTime, nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    cvss_score = Column(String(10), nullable=True)
    affected_versions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    discovered_date = Column(DateTime, default=func.now())

    
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    subscriptions = relationship("Subscription", back_populates="vulnerability")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
    
    __table_args__ = (
        UniqueConstraint('unique_id', 'oem_name', name='uix_vuln_id_oem'),
        Index('idx_oem_severity', 'oem_name', 'severity_level'),
        Index('idx_published_date', 'published_date'),
        Index('idx_product_oem', 'product_name', 'oem_name'),
    )

class Subscription(Base):
    """Model for user email and Slack subscriptions"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=True, index=True)
    slack_webhook_url = Column(String(500), nullable=True, index=True)
    oem_name = Column(String(100), nullable=True, index=True)
    product_name = Column(String(200), nullable=True, index=True)
    severity_filter = Column(String(20), nullable=False, default="Critical,High")
    is_active = Column(Boolean, default=True, nullable=False)
    created_date = Column(DateTime, default=func.now(), nullable=False)
    last_notified = Column(DateTime, nullable=True)
    
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=True)
    vulnerability = relationship("Vulnerability", back_populates="subscriptions")
    
    __table_args__ = (
        Index('idx_email_active', 'email', 'is_active'),
        Index('idx_slack_webhook', 'slack_webhook_url', 'is_active'),
        Index('idx_oem_product', 'oem_name', 'product_name'),
    )

class ScanLog(Base):
    """Model for tracking scraping operations"""
    __tablename__ = "scan_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    oem_name = Column(String(100), nullable=False, index=True)
    scan_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    vulnerabilities_found = Column(Integer, default=0, nullable=False)
    new_vulnerabilities = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    scan_duration = Column(Integer, nullable=True)
    scan_date = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_oem_scan_date', 'oem_name', 'scan_date'),
        Index('idx_scan_status', 'status', 'scan_date'),
    )

class NotificationLog(Base):
    """Model for tracking sent email and Slack notifications"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=False)
    email_sent = Column(Boolean, default=False, nullable=False)
    slack_sent = Column(Boolean, default=False, nullable=False)
    sent_date = Column(DateTime, default=func.now(), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    subscription = relationship("Subscription")
    vulnerability = relationship("Vulnerability")
    
    __table_args__ = (
        Index('idx_sent_date', 'sent_date'),
        Index('idx_subscription_vuln', 'subscription_id', 'vulnerability_id'),
    )

class AuditLog(Base):
    """Model for tracking audit trails"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=False)
    action = Column(String(50), nullable=False)
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    user = Column(String(100), default="Admin", nullable=False)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    details = Column(Text, nullable=True)
    
    vulnerability = relationship("Vulnerability")

class SystemSettings(Base):
    """Model for system-wide settings"""
    __tablename__ = "system_settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
