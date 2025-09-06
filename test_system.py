#!/usr/bin/env python3
"""
Test script for OEM Vulnerability Alert Platform
"""
import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from database import init_database, get_db
        from database.operations import DatabaseOperations
        from database.models import Vulnerability, Subscription, ScanLog
        print("✅ Database modules imported successfully")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from scrapers import create_scraper_manager, SCRAPER_REGISTRY
        print("✅ Scraper modules imported successfully")
    except Exception as e:
        print(f"❌ Scraper import failed: {e}")
        return False
    
    try:
        from email_notifications import create_email_service
        print("✅ Email modules imported successfully")
    except Exception as e:
        print(f"❌ Email import failed: {e}")
        return False
    
    try:
        from config import get_all_oems, get_enabled_oems
        print("✅ Config modules imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization and operations"""
    print("\nTesting database...")
    
    try:
        from database import init_database, get_db
        from database.operations import DatabaseOperations
        
        # Initialize database
        init_database()
        print("✅ Database initialized successfully")
        
        # Test database operations
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        
        # Test adding a sample vulnerability
        sample_vuln = {
            'unique_id': 'TEST-CVE-2024-0001',
            'product_name': 'Test Product',
            'product_version': '1.0.0',
            'oem_name': 'Test OEM',
            'severity_level': 'High',
            'vulnerability_description': 'This is a test vulnerability',
            'mitigation_strategy': 'Update to latest version',
            'published_date': datetime.now()
        }
        
        vuln = db_ops.add_vulnerability(sample_vuln)
        print(f"✅ Sample vulnerability added: {vuln.unique_id}")
        
        # Test querying vulnerabilities
        vulns = db_ops.get_vulnerabilities(limit=5)
        print(f"✅ Found {len(vulns)} vulnerabilities in database")
        
        # Test statistics
        stats = db_ops.get_vulnerability_stats()
        print(f"✅ Database statistics: {stats['total_vulnerabilities']} total vulnerabilities")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_scrapers():
    """Test scraper initialization"""
    print("\nTesting scrapers...")
    
    try:
        from scrapers import create_scraper_manager, SCRAPER_REGISTRY
        
        # Test scraper manager creation
        scraper_manager = create_scraper_manager()
        print("✅ Scraper manager created successfully")
        
        # Test scraper registry
        print(f"✅ Found {len(SCRAPER_REGISTRY)} registered scrapers:")
        for oem_id, scraper_class in SCRAPER_REGISTRY.items():
            print(f"  - {oem_id}: {scraper_class.__name__}")
        
        # Test scraper status
        status = scraper_manager.get_scraper_status()
        print(f"✅ Scraper status retrieved for {len(status)} OEMs")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import get_all_oems, get_enabled_oems
        
        # Test OEM configuration
        all_oems = get_all_oems()
        print(f"✅ Loaded {len(all_oems)} OEM configurations")
        
        enabled_oems = get_enabled_oems()
        print(f"✅ Found {len(enabled_oems)} enabled OEMs: {enabled_oems}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_email_service():
    """Test email service initialization"""
    print("\nTesting email service...")
    
    try:
        from database import get_db
        from database.operations import DatabaseOperations
        from email_notifications import create_email_service
        
        # Initialize database and email service
        db = next(get_db())
        db_ops = DatabaseOperations(db)
        email_service = create_email_service(db_ops)
        
        print("✅ Email service created successfully")
        
        # Test email configuration (without actually sending)
        print("✅ Email service configuration loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚨 OEM Vulnerability Alert Platform - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database),
        ("Scraper Test", test_scrapers),
        ("Config Test", test_config),
        ("Email Service Test", test_email_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Run 'python setup_database.py setup' to initialize the database")
        print("2. Edit .env file with your email configuration")
        print("3. Run 'streamlit run app.py' to start the web interface")
        print("4. Run './setup.sh' to set up automated scanning")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
