from database import init_database, get_db
from database.operations import DatabaseOperations
from database.models import Organization, User, Vulnerability
from datetime import datetime

def verify_rbac():
    init_database()
    db = next(get_db())
    ops = DatabaseOperations(db)
    
    print("Setting up test data...")
    
    # Create Org
    org = ops.create_organization("RBAC Test Org")
    if not org:
        org = db.query(Organization).filter_by(name="RBAC Test Org").first()
    
    # Use existing user or create one
    user = ops.get_user_by_email("rbac_test@example.com")
    if not user:
        user = ops.create_user("rbac_test", "rbac_test@example.com", "password", "Analyst", org.id)
    
    # Set Allowed OEMs
    print(f"Updating Org {org.name} allowed OEMs to ['Red Hat']...")
    ops.update_organization_oems(org.id, ["Red Hat"])
    
    # Verify DB state
    updated_org = ops.get_organization(org.id)
    print(f"Org Enabled OEMs: {updated_org.enabled_oems}")
    assert updated_org.enabled_oems == "Red Hat"
    
    # Add dummy vulnerabilites
    v1 = {
        "unique_id": "TEST-RH-001",
        "product_name": "RHEL",
        "oem_name": "Red Hat",
        "severity_level": "Critical",
        "vulnerability_description": "Test RH Vuln",
        "published_date": datetime.now()
    }
    v2 = {
        "unique_id": "TEST-PA-001",
        "product_name": "Firewall",
        "oem_name": "Palo Alto",
        "severity_level": "High",
        "vulnerability_description": "Test PA Vuln",
        "published_date": datetime.now()
    }
    
    ops.add_vulnerability(v1)
    ops.add_vulnerability(v2)
    
    # Test Filtering
    print("Testing filtering...")
    
    # 1. No Filter (Admin view / All)
    all_vulns = ops.get_vulnerabilities(limit=100)
    print(f"Total Vulns (No Filter): {len(all_vulns)}")
    
    # 2. Filtered by 'Red Hat'
    filtered_vulns = ops.get_vulnerabilities(allowed_oems=['Red Hat'], limit=100)
    print(f"Total Vulns (Filter=['Red Hat']): {len(filtered_vulns)}")
    
    rhel_found = any(v.oem_name == "Red Hat" for v in filtered_vulns)
    pa_found = any(v.oem_name == "Palo Alto" for v in filtered_vulns)
    
    print(f"Red Hat Found: {rhel_found}")
    print(f"Palo Alto Found: {pa_found}")
    
    if rhel_found and not pa_found:
        print("SUCCESS: Filtering Logic Verified!")
    else:
        print("FAILURE: Filtering Logic Incorrect.")

if __name__ == "__main__":
    verify_rbac()
