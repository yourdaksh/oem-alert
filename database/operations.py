"""
Database operations and utilities
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from database.models import Vulnerability, Subscription, ScanLog, NotificationLog
import json

class DatabaseOperations:
    """Class for handling database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Vulnerability operations
    def add_vulnerability(self, vuln_data: Dict[str, Any]) -> Vulnerability:
        """Add a new vulnerability to the database"""
        # Check if vulnerability already exists
        existing = self.db.query(Vulnerability).filter(
            Vulnerability.unique_id == vuln_data['unique_id']
        ).first()
        
        if existing:
            return existing
        
        vulnerability = Vulnerability(**vuln_data)
        self.db.add(vulnerability)
        self.db.commit()
        self.db.refresh(vulnerability)
        return vulnerability
    
    def get_vulnerabilities(self, 
                          oem_name: Optional[str] = None,
                          severity: Optional[str] = None,
                          product_name: Optional[str] = None,
                          days_back: Optional[int] = None,
                          limit: int = 100) -> List[Vulnerability]:
        """Get vulnerabilities with optional filters"""
        query = self.db.query(Vulnerability)
        
        if oem_name:
            query = query.filter(Vulnerability.oem_name == oem_name)
        
        if severity:
            query = query.filter(Vulnerability.severity_level == severity)
        
        if product_name:
            query = query.filter(Vulnerability.product_name.ilike(f"%{product_name}%"))
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            query = query.filter(Vulnerability.published_date >= cutoff_date)
        
        return query.order_by(desc(Vulnerability.published_date)).limit(limit).all()
    
    def search_vulnerabilities(self, search_term: str, limit: int = 50) -> List[Vulnerability]:
        """Search vulnerabilities by keyword"""
        query = self.db.query(Vulnerability).filter(
            or_(
                Vulnerability.product_name.ilike(f"%{search_term}%"),
                Vulnerability.vulnerability_description.ilike(f"%{search_term}%"),
                Vulnerability.unique_id.ilike(f"%{search_term}%")
            )
        )
        return query.order_by(desc(Vulnerability.published_date)).limit(limit).all()
    
    def get_vulnerability_stats(self) -> Dict[str, Any]:
        """Get vulnerability statistics"""
        total_vulns = self.db.query(Vulnerability).count()
        
        # By severity
        severity_counts = self.db.query(
            Vulnerability.severity_level,
            func.count(Vulnerability.id)
        ).group_by(Vulnerability.severity_level).all()
        
        # By OEM
        oem_counts = self.db.query(
            Vulnerability.oem_name,
            func.count(Vulnerability.id)
        ).group_by(Vulnerability.oem_name).order_by(desc(func.count(Vulnerability.id))).all()
        
        # Recent vulnerabilities (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_count = self.db.query(Vulnerability).filter(
            Vulnerability.published_date >= recent_cutoff
        ).count()
        
        return {
            'total_vulnerabilities': total_vulns,
            'recent_vulnerabilities': recent_count,
            'severity_distribution': dict(severity_counts),
            'oem_distribution': dict(oem_counts)
        }
    
    # Subscription operations
    def add_subscription(self, email: str, oem_name: Optional[str] = None,
                        product_name: Optional[str] = None,
                        severity_filter: str = "Critical,High") -> Subscription:
        """Add a new email subscription"""
        subscription = Subscription(
            email=email,
            oem_name=oem_name,
            product_name=product_name,
            severity_filter=severity_filter
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription
    
    def get_subscriptions(self, email: Optional[str] = None) -> List[Subscription]:
        """Get subscriptions, optionally filtered by email"""
        query = self.db.query(Subscription).filter(Subscription.is_active == True)
        
        if email:
            query = query.filter(Subscription.email == email)
        
        return query.all()
    
    def update_subscription(self, subscription_id: int, **kwargs) -> Optional[Subscription]:
        """Update a subscription"""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if subscription:
            for key, value in kwargs.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            self.db.commit()
            self.db.refresh(subscription)
        
        return subscription
    
    def delete_subscription(self, subscription_id: int) -> bool:
        """Delete a subscription"""
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if subscription:
            self.db.delete(subscription)
            self.db.commit()
            return True
        return False
    
    def get_subscriptions_for_vulnerability(self, vulnerability: Vulnerability) -> List[Subscription]:
        """Get all subscriptions that should be notified about a vulnerability"""
        subscriptions = []
        
        # Get all active subscriptions
        all_subs = self.db.query(Subscription).filter(Subscription.is_active == True).all()
        
        for sub in all_subs:
            # Check if subscription matches this vulnerability
            if self._subscription_matches_vulnerability(sub, vulnerability):
                subscriptions.append(sub)
        
        return subscriptions
    
    def _subscription_matches_vulnerability(self, subscription: Subscription, 
                                          vulnerability: Vulnerability) -> bool:
        """Check if a subscription should be notified about a vulnerability"""
        # Check OEM match
        if subscription.oem_name and subscription.oem_name != vulnerability.oem_name:
            return False
        
        # Check product match
        if subscription.product_name and subscription.product_name.lower() not in vulnerability.product_name.lower():
            return False
        
        # Check severity match
        allowed_severities = [s.strip() for s in subscription.severity_filter.split(',')]
        if vulnerability.severity_level not in allowed_severities:
            return False
        
        return True
    
    # Scan log operations
    def log_scan(self, oem_name: str, scan_type: str, status: str,
                vulnerabilities_found: int = 0, new_vulnerabilities: int = 0,
                error_message: Optional[str] = None, scan_duration: Optional[int] = None):
        """Log a scanning operation"""
        scan_log = ScanLog(
            oem_name=oem_name,
            scan_type=scan_type,
            status=status,
            vulnerabilities_found=vulnerabilities_found,
            new_vulnerabilities=new_vulnerabilities,
            error_message=error_message,
            scan_duration=scan_duration
        )
        self.db.add(scan_log)
        self.db.commit()
    
    def get_recent_scans(self, limit: int = 50) -> List[ScanLog]:
        """Get recent scan logs"""
        return self.db.query(ScanLog).order_by(desc(ScanLog.scan_date)).limit(limit).all()
    
    def get_scan_stats(self) -> Dict[str, Any]:
        """Get scanning statistics"""
        total_scans = self.db.query(ScanLog).count()
        successful_scans = self.db.query(ScanLog).filter(ScanLog.status == 'success').count()
        error_scans = self.db.query(ScanLog).filter(ScanLog.status == 'error').count()
        
        # Last scan times by OEM
        last_scans = self.db.query(
            ScanLog.oem_name,
            func.max(ScanLog.scan_date)
        ).group_by(ScanLog.oem_name).all()
        
        return {
            'total_scans': total_scans,
            'successful_scans': successful_scans,
            'error_scans': error_scans,
            'success_rate': (successful_scans / total_scans * 100) if total_scans > 0 else 0,
            'last_scans_by_oem': dict(last_scans)
        }
    
    # Notification log operations
    def log_notification(self, subscription_id: int, vulnerability_id: int,
                        email_sent: bool = True, error_message: Optional[str] = None):
        """Log a sent notification"""
        notification_log = NotificationLog(
            subscription_id=subscription_id,
            vulnerability_id=vulnerability_id,
            email_sent=email_sent,
            error_message=error_message
        )
        self.db.add(notification_log)
        self.db.commit()
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_notifications = self.db.query(NotificationLog).count()
        successful_notifications = self.db.query(NotificationLog).filter(
            NotificationLog.email_sent == True
        ).count()
        
        # Notifications by day (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_notifications = self.db.query(NotificationLog).filter(
            NotificationLog.sent_date >= recent_cutoff
        ).count()
        
        return {
            'total_notifications': total_notifications,
            'successful_notifications': successful_notifications,
            'recent_notifications': recent_notifications,
            'success_rate': (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0
        }
