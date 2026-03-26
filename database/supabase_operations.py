import os
import logging
from typing import Dict, Any, Optional
from backend.dependencies import get_supabase

logger = logging.getLogger(__name__)

class SupabaseOperations:
    """Class for handling database operations using Supabase PostgreSQL"""
    
    def __init__(self):
        self.supabase = get_supabase()
        if not self.supabase:
            logger.error("Supabase client not initialized. SCRAPERS WILL FAIL TO SAVE.")

    def add_vulnerability(self, vuln_data: Dict[str, Any]) -> Any:
        """Add a new vulnerability to the Supabase database"""
        if not self.supabase:
            return None
            
        try:
            existing = self.supabase.table('vulnerabilities').select('id, unique_id, discovered_date').eq('unique_id', vuln_data['unique_id']).execute()
            
            if existing.data and len(existing.data) > 0:
                class ExistingRecord:
                    def __init__(self, data):
                        self.unique_id = data['unique_id']
                        from datetime import datetime
                        if isinstance(data.get('discovered_date'), str):
                            try:
                                self.discovered_date = datetime.fromisoformat(data['discovered_date'].replace('Z', '+00:00'))
                            except Exception:
                                self.discovered_date = datetime.now()
                        else:
                            self.discovered_date = data.get('discovered_date', datetime.now())
                            
                return ExistingRecord(existing.data[0])
            
            insert_data = vuln_data.copy()
            for k, v in insert_data.items():
                if hasattr(v, 'isoformat'):
                    insert_data[k] = v.isoformat()
            
            mapped_data = {
                'unique_id': insert_data.get('unique_id'),
                'product_name': insert_data.get('product_name'),
                'oem_name': insert_data.get('oem_name'),
                'severity_level': insert_data.get('severity_level'),
                'description': insert_data.get('vulnerability_description', ''), # Mapped key
                'mitigation': insert_data.get('mitigation_strategy', ''),       # Mapped key
                'source_url': insert_data.get('source_url'),
                'cvss_score': str(insert_data.get('cvss_score')) if insert_data.get('cvss_score') else None,
                'affected_versions': insert_data.get('affected_versions')
            }
            
            result = self.supabase.table('vulnerabilities').insert(mapped_data).execute()
            
            if result.data and len(result.data) > 0:
                class NewRecord:
                    def __init__(self, data):
                        self.unique_id = data['unique_id']
                        from datetime import datetime
                        try:
                            self.discovered_date = datetime.fromisoformat(data['discovered_date'].replace('Z', '+00:00'))
                        except Exception:
                            self.discovered_date = datetime.now()
                return NewRecord(result.data[0])
                
        except Exception as e:
            logger.error(f"Error adding vulnerability to Supabase: {e}")
            return None

    def log_scan(self, oem_name: str, scan_type: str, status: str,
                vulnerabilities_found: int = 0, new_vulnerabilities: int = 0,
                error_message: Optional[str] = None, scan_duration: Optional[int] = None):
        """Log a scanning operation. We don't have a direct scan_logs table in Supabase right now.
           If necessary, we can log to a generic logs table or just standard stdout."""
        logger.info(f"Supabase SCAN LOG: {oem_name} | {scan_type} | {status} | Found: {vulnerabilities_found} | New: {new_vulnerabilities} | Error: {error_message}")
