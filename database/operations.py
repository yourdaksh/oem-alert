"""
Database operations and utilities
"""
from .models import Base, Vulnerability, Subscription, NotificationLog, ScanLog, AuditLog, SystemSettings, User, Organization, Invitation
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, create_engine
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import json
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """Class for handling database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Vulnerability operations
    def set_resolution_notes(self, vuln_id: int, notes: str) -> bool:
        """Update resolution notes for a vulnerability"""
        try:
            vuln = self.db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
            if vuln:
                vuln.resolution_notes = notes
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting resolution notes: {e}")
            self.db.rollback()
            return False

    def update_vulnerability_status(self, vulnerability_id: int, new_status: str, 
                                  user: str = "Admin", details: Optional[str] = None) -> Optional[Vulnerability]:
        """Update vulnerability status and create audit log"""
        vulnerability = self.db.query(Vulnerability).filter(
            Vulnerability.id == vulnerability_id
        ).first()
        
        if vulnerability:
            old_status = vulnerability.status
            if old_status != new_status:
                vulnerability.status = new_status
                
                # Create audit log
                audit_log = AuditLog(
                    vulnerability_id=vulnerability.id,
                    action="status_change",
                    old_value=old_status,
                    new_value=new_status,
                    user=user,
                    details=details
                )
                self.db.add(audit_log)
                
                self.db.commit()
                self.db.refresh(vulnerability)
        
        return vulnerability

    def get_audit_logs(self, vulnerability_id: int) -> List[AuditLog]:
        """Get audit logs for a vulnerability"""
        return self.db.query(AuditLog).filter(
            AuditLog.vulnerability_id == vulnerability_id
        ).order_by(desc(AuditLog.timestamp)).all()

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
                          allowed_oems: Optional[List[str]] = None,
                          limit: int = 100) -> List[Vulnerability]:
        """Get vulnerabilities with optional filters"""
        query = self.db.query(Vulnerability)
        
        if oem_name:
            query = query.filter(Vulnerability.oem_name == oem_name)
            
        if allowed_oems:
            query = query.filter(Vulnerability.oem_name.in_(allowed_oems))
        
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
    
    def get_vulnerability_stats(self, allowed_oems: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get vulnerability statistics"""
        vuln_query = self.db.query(Vulnerability)
        if allowed_oems:
            vuln_query = vuln_query.filter(Vulnerability.oem_name.in_(allowed_oems))
            
        total_vulns = vuln_query.count()
        
        # By severity
        severity_query = self.db.query(
            Vulnerability.severity_level,
            func.count(Vulnerability.id)
        )
        if allowed_oems:
            severity_query = severity_query.filter(Vulnerability.oem_name.in_(allowed_oems))
        
        severity_counts = severity_query.group_by(Vulnerability.severity_level).all()
        
        # By OEM
        oem_query = self.db.query(
            Vulnerability.oem_name,
            func.count(Vulnerability.id)
        )
        if allowed_oems:
            oem_query = oem_query.filter(Vulnerability.oem_name.in_(allowed_oems))
            
        oem_counts = oem_query.group_by(Vulnerability.oem_name).order_by(desc(func.count(Vulnerability.id))).all()
        
        # Recent vulnerabilities (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_query = self.db.query(Vulnerability).filter(
            Vulnerability.published_date >= recent_cutoff
        )
        if allowed_oems:
            recent_query = recent_query.filter(Vulnerability.oem_name.in_(allowed_oems))
            
        recent_count = recent_query.count()
        
        return {
            'total_vulnerabilities': total_vulns,
            'recent_vulnerabilities': recent_count,
            'severity_distribution': dict(severity_counts),
            'oem_distribution': dict(oem_counts)
        }
    
    # Subscription operations
    def add_subscription(self, email: Optional[str] = None, 
                        slack_webhook_url: Optional[str] = None,
                        oem_name: Optional[str] = None,
                        product_name: Optional[str] = None,
                        severity_filter: str = "Critical,High") -> Subscription:
        """Add a new email or Slack subscription"""
        if not email and not slack_webhook_url:
            raise ValueError("Either email or slack_webhook_url must be provided")
        
        subscription = Subscription(
            email=email,
            slack_webhook_url=slack_webhook_url,
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
                        email_sent: bool = False, slack_sent: bool = False, 
                        error_message: Optional[str] = None):
        """Log a sent notification"""
        notification_log = NotificationLog(
            subscription_id=subscription_id,
            vulnerability_id=vulnerability_id,
            email_sent=email_sent,
            slack_sent=slack_sent,
            error_message=error_message
        )
        self.db.add(notification_log)
        self.db.commit()
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_notifications = self.db.query(NotificationLog).count()
        successful_email = self.db.query(NotificationLog).filter(
            NotificationLog.email_sent == True
        ).count()
        successful_slack = self.db.query(NotificationLog).filter(
            NotificationLog.slack_sent == True
        ).count()
        total_successful = successful_email + successful_slack
        
        # Notifications by day (last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_notifications = self.db.query(NotificationLog).filter(
            NotificationLog.sent_date >= recent_cutoff
        ).count()
        
        return {
            'total_notifications': total_notifications,
            'total_sent': total_notifications, # Alias for UI compatibility
            'successful_notifications': total_successful,
            'email_notifications': successful_email,
            'slack_notifications': successful_slack,

            'recent_notifications': recent_notifications,
            'success_rate': (total_successful / total_notifications * 100) if total_notifications > 0 else 0
        }

    # System Settings operations
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a system setting value"""
        from database.models import SystemSettings
        setting = self.db.query(SystemSettings).filter(SystemSettings.key == key).first()
        return setting.value if setting else default
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set a system setting value"""
        from database.models import SystemSettings, Organization, User, Invitation, AuditLog
        import hashlib
        import secrets
        import datetime
        import logging
        
        logger = logging.getLogger(__name__)

        setting = self.db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = SystemSettings(key=key, value=value)
            self.db.add(setting)
        self.db.commit()
        return True

    # --- CRM / User Management ---

    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2"""
        salt = secrets.token_hex(16)
        return self._hash_password_with_salt(password, salt)

    def _hash_password_with_salt(self, password: str, salt: str) -> str:
        """Helper to hash with specific salt"""
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return f"{salt}${key.hex()}"

    def _verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verify a stored password against provided password"""
        try:
            salt, key = stored_password.split('$')
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return new_key.hex() == key
        except ValueError:
            return False

    def create_organization(self, name: str, owner_id: int = None) -> Optional[Organization]:
        """Create a new organization"""
        try:
            org = Organization(name=name, owner_id=owner_id)
            self.db.add(org)
            self.db.commit()
            return org
        except Exception as e:
            logger.error(f"Error creating organization: {e}")
            self.db.rollback()
            return None
            
    def update_organization_oems(self, org_id: int, enabled_oems: List[str]) -> bool:
        """Update the list of enabled OEMs for an organization"""
        try:
            org = self.get_organization(org_id)
            if org:
                # Convert list to comma-separated string
                org.enabled_oems = ",".join(enabled_oems)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating organization OEMs: {e}")
            self.db.rollback()
            return False

    def get_organization(self, org_id: int) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, username: str, email: str, password: str, role: str = "Analyst", org_id: int = None) -> Optional[User]:
        """Create a new user"""
        try:
            pwd_hash = self._hash_password(password)
            user = User(
                username=username,
                email=email,
                password_hash=pwd_hash,
                role=role,
                organization_id=org_id
            )
            self.db.add(user)
            self.db.commit()
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            self.db.rollback()
            return None

    def verify_login(self, email: str, password: str) -> Optional[User]:
        """Verify login credentials"""
        user = self.get_user_by_email(email)
        if user and user.password_hash:
            if self._verify_password(user.password_hash, password):
                return user
        return None

    def create_invitation(self, email: str, org_id: int, role: str = "Analyst") -> Optional[Invitation]:
        """Create an invitation for a user to join an org"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        try:
            invite = Invitation(
                email=email,
                organization_id=org_id,
                role=role,
                token=token,
                expires_at=expires_at
            )
            self.db.add(invite)
            self.db.commit()
            return invite
        except Exception as e:
            logger.error(f"Error creating invitation: {e}")
            self.db.rollback()
            return None

    def get_invitation_by_token(self, token: str) -> Optional[Invitation]:
        return self.db.query(Invitation).filter(
            Invitation.token == token,
            Invitation.status == 'Pending',
            Invitation.expires_at > datetime.utcnow()
        ).first()

    def accept_invitation(self, token: str, username: str, password: str) -> Optional[User]:
        """Accept an invitation and create the user"""
        invite = self.get_invitation_by_token(token)
        if not invite:
            return None
        
        # Create user
        user = self.create_user(
            username=username,
            email=invite.email,
            password=password,
            role=invite.role,
            org_id=invite.organization_id
        )
        
        if user:
            # Mark invite as accepted
            invite.status = 'Accepted'
            self.db.commit()
            return user
        return None

    def get_organization_users(self, org_id: int) -> List[User]:
        return self.db.query(User).filter(User.organization_id == org_id).all()

    def assign_vulnerability(self, vuln_id: int, assigned_to_id: int, assigned_by_id: int) -> bool:
        """Assign a vulnerability to a user"""
        try:
            logger.info(f"Attempting to assign vuln {vuln_id} to user {assigned_to_id} by user {assigned_by_id}")
            
            vuln = self.db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
            if not vuln:
                logger.error(f"Vulnerability {vuln_id} not found")
                return False
            
            logger.info(f"Found vulnerability: {vuln.unique_id}")
            
            old_status = vuln.status
            vuln.assigned_to_id = assigned_to_id
            vuln.assigned_by_id = assigned_by_id
            vuln.assigned_at = datetime.utcnow()
            vuln.status = "Assigned"
            
            # Log this action
            audit_log = AuditLog(
                vulnerability_id=vuln.id,
                action="assignment",
                old_value=old_status,
                new_value="Assigned",
                user=f"User ID {assigned_by_id}", # Ideally we fetch username
                details=f"Assigned to User ID {assigned_to_id}"
            )
            self.db.add(audit_log)
            
            logger.info("Committing assignment to database...")
            self.db.commit()
            logger.info("Assignment successful!")
            return True
        except Exception as e:
            logger.error(f"Error assigning vulnerability: {e}", exc_info=True)
            self.db.rollback()
            return False

    def get_user_assigned_vulnerabilities(self, user_id: int) -> List[Vulnerability]:
        """Get vulnerabilities assigned to a user"""
        return self.db.query(Vulnerability).filter(Vulnerability.assigned_to_id == user_id).all()
