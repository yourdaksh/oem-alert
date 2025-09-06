#!/usr/bin/env python3
"""
Test scraper functionality with mock data
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_database, get_db
from database.operations import DatabaseOperations
from database.models import Vulnerability

def create_mock_vulnerabilities():
    """Create mock vulnerability data for testing"""
    
    # Initialize database
    init_database()
    db = next(get_db())
    db_ops = DatabaseOperations(db)
    
    # Mock vulnerability data
    mock_vulns = [
        {
            'unique_id': 'CVE-2024-0001',
            'product_name': 'Windows 11',
            'product_version': '22H2',
            'oem_name': 'Microsoft',
            'severity_level': 'Critical',
            'vulnerability_description': 'Remote code execution vulnerability in Windows kernel',
            'mitigation_strategy': 'Apply security update KB5034441',
            'published_date': datetime.now() - timedelta(days=1),
            'source_url': 'https://msrc.microsoft.com/update-guide/vulnerability/CVE-2024-0001',
            'cvss_score': '9.8'
        },
        {
            'unique_id': 'CVE-2024-0002',
            'product_name': 'Cisco IOS',
            'product_version': '15.7',
            'oem_name': 'Cisco',
            'severity_level': 'High',
            'vulnerability_description': 'Buffer overflow in HTTP server component',
            'mitigation_strategy': 'Upgrade to IOS 15.8 or later',
            'published_date': datetime.now() - timedelta(days=2),
            'source_url': 'https://tools.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-20240002',
            'cvss_score': '8.5'
        },
        {
            'unique_id': 'CVE-2024-0003',
            'product_name': 'Intel Management Engine',
            'product_version': '11.0',
            'oem_name': 'Intel',
            'severity_level': 'High',
            'vulnerability_description': 'Privilege escalation vulnerability in ME firmware',
            'mitigation_strategy': 'Update ME firmware to version 11.1',
            'published_date': datetime.now() - timedelta(days=3),
            'source_url': 'https://www.intel.com/content/www/us/en/security-center/advisory/intel-sa-20240003.html',
            'cvss_score': '7.8'
        },
        {
            'unique_id': 'CVE-2024-0004',
            'product_name': 'Oracle Database',
            'product_version': '19c',
            'oem_name': 'Oracle',
            'severity_level': 'Critical',
            'vulnerability_description': 'SQL injection vulnerability in Oracle Database',
            'mitigation_strategy': 'Apply Oracle Critical Patch Update',
            'published_date': datetime.now() - timedelta(days=4),
            'source_url': 'https://www.oracle.com/security-alerts/cpujan2024.html',
            'cvss_score': '9.1'
        },
        {
            'unique_id': 'CVE-2024-0005',
            'product_name': 'VMware vSphere',
            'product_version': '7.0',
            'oem_name': 'VMware',
            'severity_level': 'High',
            'vulnerability_description': 'Authentication bypass in vCenter Server',
            'mitigation_strategy': 'Update to vSphere 7.0 Update 3',
            'published_date': datetime.now() - timedelta(days=5),
            'source_url': 'https://www.vmware.com/security/advisories/VMSA-2024-0001.html',
            'cvss_score': '8.2'
        }
    ]
    
    print("Creating mock vulnerability data...")
    
    added_count = 0
    for vuln_data in mock_vulns:
        try:
            vuln = db_ops.add_vulnerability(vuln_data)
            print(f"✅ Added: {vuln.unique_id} - {vuln.product_name} ({vuln.severity_level})")
            added_count += 1
        except Exception as e:
            print(f"❌ Failed to add {vuln_data['unique_id']}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   - Added {added_count} vulnerabilities")
    
    # Get statistics
    stats = db_ops.get_vulnerability_stats()
    print(f"   - Total vulnerabilities in database: {stats['total_vulnerabilities']}")
    print(f"   - By severity: {stats['severity_distribution']}")
    print(f"   - By OEM: {stats['oem_distribution']}")
    
    return added_count

def test_database_queries():
    """Test database query functionality"""
    print("\n🔍 Testing database queries...")
    
    db = next(get_db())
    db_ops = DatabaseOperations(db)
    
    # Test different filters
    print("\n1. All vulnerabilities:")
    all_vulns = db_ops.get_vulnerabilities(limit=10)
    print(f"   Found {len(all_vulns)} vulnerabilities")
    
    print("\n2. Critical vulnerabilities only:")
    critical_vulns = db_ops.get_vulnerabilities(severity="Critical", limit=10)
    print(f"   Found {len(critical_vulns)} critical vulnerabilities")
    
    print("\n3. Microsoft vulnerabilities only:")
    ms_vulns = db_ops.get_vulnerabilities(oem_name="Microsoft", limit=10)
    print(f"   Found {len(ms_vulns)} Microsoft vulnerabilities")
    
    print("\n4. Recent vulnerabilities (last 7 days):")
    recent_vulns = db_ops.get_vulnerabilities(days_back=7, limit=10)
    print(f"   Found {len(recent_vulns)} recent vulnerabilities")
    
    print("\n5. Search by keyword 'Windows':")
    search_results = db_ops.search_vulnerabilities("Windows")
    print(f"   Found {len(search_results)} vulnerabilities matching 'Windows'")

def main():
    """Main test function"""
    print("🧪 Mock Vulnerability Data Test")
    print("=" * 40)
    
    try:
        # Create mock data
        added_count = create_mock_vulnerabilities()
        
        if added_count > 0:
            # Test queries
            test_database_queries()
            
            print("\n✅ Mock data test completed successfully!")
            print("\nNext steps:")
            print("1. Run 'streamlit run app.py' to view the dashboard")
            print("2. Check the vulnerabilities in the web interface")
            print("3. Test filtering and search functionality")
        else:
            print("❌ No mock data was added. Check the errors above.")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
