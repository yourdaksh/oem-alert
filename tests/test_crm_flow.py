
import sys
import os
import unittest
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, User, Organization, Invitation, Vulnerability, AuditLog
from database.operations import DatabaseOperations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestCRMFlow(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.db_ops = DatabaseOperations(self.session)
        
    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_organization_and_user_creation(self):
        print("\nTesting Organization and User Creation...")
        # 1. Create Org
        org = self.db_ops.create_organization("Cyber Defense Force")
        self.assertIsNotNone(org)
        print(f"Created Org: {org.name} (ID: {org.id})")
        
        # 2. Create Owner
        owner = self.db_ops.create_user("alice", "alice@example.com", "password123", "Owner", org.id)
        self.assertIsNotNone(owner)
        print(f"Created Owner: {owner.username} (ID: {owner.id})")
        
        # Verify Owner is linked to Org
        self.assertEqual(owner.organization_id, org.id)
        
        # Verify Login
        logged_in = self.db_ops.verify_login("alice@example.com", "password123")
        self.assertIsNotNone(logged_in)
        self.assertEqual(logged_in.id, owner.id)
        print("Login Verified.")

    def test_invitation_flow(self):
        print("\nTesting Invitation Flow...")
        org = self.db_ops.create_organization("SecOps Inc")
        owner = self.db_ops.create_user("admin", "admin@secops.com", "pass", "Owner", org.id)
        
        # 1. Create Invitation
        invite = self.db_ops.create_invitation("bob@secops.com", org.id, "Analyst")
        self.assertIsNotNone(invite)
        self.assertEqual(invite.status, "Pending")
        print(f"Created Invitation Token: {invite.token}")
        
        # 2. Retrieve Invitation
        retrieved_invite = self.db_ops.get_invitation_by_token(invite.token)
        self.assertIsNotNone(retrieved_invite)
        self.assertEqual(retrieved_invite.email, "bob@secops.com")
        
        # 3. Accept Invitation
        new_user = self.db_ops.accept_invitation(invite.token, "bob", "bobpass")
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, "bob@secops.com")
        self.assertEqual(new_user.organization_id, org.id)
        print(f"User {new_user.username} accepted invitation and joined Org {org.id}")
        
        # Verify Invite Status
        self.session.refresh(invite)
        self.assertEqual(invite.status, "Accepted")

    def test_assignment_flow(self):
        print("\nTesting Assignment Flow...")
        org = self.db_ops.create_organization("ThreatTeam")
        lead = self.db_ops.create_user("lead", "lead@tt.com", "pass", "Team Lead", org.id)
        analyst = self.db_ops.create_user("grunt", "grunt@tt.com", "pass", "Analyst", org.id)
        
        # 1. Create Vulnerability
        vuln = Vulnerability(
            unique_id="CVE-2024-9999",
            product_name="TestProduct",
            oem_name="TestOEM",
            severity_level="Critical",
            published_date=datetime.now(),
            vulnerability_description="Bad bug",
            status="Open",
            organization_id=org.id
        )
        self.session.add(vuln)
        self.session.commit()
        
        # 2. Assign Vulnerability
        success = self.db_ops.assign_vulnerability(vuln.id, analyst.id, lead.id)
        self.assertTrue(success)
        
        # 3. Verify Assignment
        self.session.refresh(vuln)
        self.assertEqual(vuln.assigned_to_id, analyst.id)
        self.assertEqual(vuln.assigned_by_id, lead.id)
        self.assertEqual(vuln.status, "Assigned")
        print(f"Vulnerability {vuln.unique_id} assigned to {analyst.username} by {lead.username}")
        
        # 4. Verify Audit Log
        logs = self.session.query(AuditLog).filter(AuditLog.vulnerability_id == vuln.id).all()
        self.assertTrue(len(logs) > 0)
        self.assertEqual(logs[0].action, "assignment")
        print("Audit Log Entry Verified.")
        
        # 5. Verify "My Tasks" retrieval
        tasks = self.db_ops.get_user_assigned_vulnerabilities(analyst.id)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, vuln.id)
        print("My Tasks Retrieval Verified.")

    def test_notes_update(self):
        print("\nTesting Resolution Notes...")
        org = self.db_ops.create_organization("NotesOrg")
        user = self.db_ops.create_user("noter", "note@org.com", "pass", "Analyst", org.id)
        
        vuln = Vulnerability(
             unique_id="CVE-NOTE-01",
             product_name="NoteProd",
             oem_name="NoteOEM",
             severity_level="Low",
             published_date=datetime.now(),
             vulnerability_description="Note bug",
             organization_id=org.id
        )
        self.session.add(vuln)
        self.session.commit()
        
        # Update Notes
        self.db_ops.set_resolution_notes(vuln.id, "Fixed by patching.")
        
        self.session.refresh(vuln)
        self.assertEqual(vuln.resolution_notes, "Fixed by patching.")
        print("Resolution Notes Verified.")

if __name__ == '__main__':
    unittest.main()
