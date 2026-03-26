"""
Main scraper runner script for automated vulnerability scanning
"""
import sys
import os
import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_operations import SupabaseOperations
from database.models import Vulnerability, ScanLog
from scrapers import create_scraper_manager
from config import get_enabled_oems

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_scrapers():
    """Run all enabled scrapers and process results"""
    logger.info("Starting vulnerability scraping process to Supabase")
    
    try:
        db_ops = SupabaseOperations()
        
        scraper_manager = create_scraper_manager()
        enabled_oems = get_enabled_oems()
        logger.info(f"Enabled OEMs: {enabled_oems}")
        
        results = scraper_manager.run_all_scrapers()
        
        total_vulnerabilities = 0
        total_new_vulnerabilities = 0
        total_notifications_sent = 0
        
        for oem_id, vulnerabilities in results.items():
            logger.info(f"Processing {len(vulnerabilities)} vulnerabilities for {oem_id}")
            
            new_vulns_count = 0
            error_count = 0
            
            for vuln_data in vulnerabilities:
                try:
                    vulnerability = db_ops.add_vulnerability(vuln_data)
                    total_vulnerabilities += 1
                    
                    if vulnerability.discovered_date.date() == datetime.now().date():
                        new_vulns_count += 1
                        total_new_vulnerabilities += 1
                        
                        logger.info(f"New vulnerability {vulnerability.unique_id} - Cloud notifications will handle this.")
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing vulnerability {vuln_data.get('unique_id', 'unknown')}: {e}")
            
            db_ops.log_scan(
                oem_name=oem_id,
                scan_type='scheduled',
                status='success' if error_count == 0 else 'partial',
                vulnerabilities_found=len(vulnerabilities),
                new_vulnerabilities=new_vulns_count,
                error_message=f"{error_count} errors" if error_count > 0 else None
            )
        
        logger.info(f"Scraping completed:")
        logger.info(f"  - Total vulnerabilities processed: {total_vulnerabilities}")
        logger.info(f"  - New vulnerabilities: {total_new_vulnerabilities}")
        logger.info(f"  - Email notifications sent: {total_notifications_sent}")
        
        return {
            'total_vulnerabilities': total_vulnerabilities,
            'new_vulnerabilities': total_new_vulnerabilities,
            'notifications_sent': total_notifications_sent,
            'oems_scanned': len(enabled_oems)
        }
        
    except Exception as e:
        logger.error(f"Fatal error in scraping process: {e}")
        
        try:
            db_ops.log_scan(
                oem_name='system',
                scan_type='scheduled',
                status='error',
                vulnerabilities_found=0,
                new_vulnerabilities=0,
                error_message=str(e)
            )
        except:
            pass
        
        raise

def run_single_oem_scraper(oem_id: str):
    """Run scraper for a single OEM"""
    logger.info(f"Running scraper for {oem_id}")
    
    try:
        db_ops = SupabaseOperations()
        
        scraper_manager = create_scraper_manager()
        vulnerabilities = scraper_manager.run_scraper(oem_id)
        
        new_vulns_count = 0
        notifications_sent = 0
        
        for vuln_data in vulnerabilities:
            try:
                vulnerability = db_ops.add_vulnerability(vuln_data)
                
                if vulnerability.discovered_date.date() == datetime.now().date():
                    new_vulns_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing vulnerability: {e}")
        
        db_ops.log_scan(
            oem_name=oem_id,
            scan_type='manual',
            status='success',
            vulnerabilities_found=len(vulnerabilities),
            new_vulnerabilities=new_vulns_count
        )
        
        logger.info(f"Single OEM scan completed for {oem_id}: {len(vulnerabilities)} vulnerabilities, {new_vulns_count} new")
        
        return {
            'oem': oem_id,
            'vulnerabilities_found': len(vulnerabilities),
            'new_vulnerabilities': new_vulns_count,
            'notifications_sent': notifications_sent
        }
        
    except Exception as e:
        logger.error(f"Error running single OEM scraper for {oem_id}: {e}")
        
        try:
            db_ops.log_scan(
                oem_name=oem_id,
                scan_type='manual',
                status='error',
                vulnerabilities_found=0,
                new_vulnerabilities=0,
                error_message=str(e)
            )
        except:
            pass
        
        raise

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        oem_id = sys.argv[1]
        try:
            result = run_single_oem_scraper(oem_id)
            print(f"Scan completed for {oem_id}: {result}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        try:
            result = run_scrapers()
            print(f"Scan completed: {result}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
