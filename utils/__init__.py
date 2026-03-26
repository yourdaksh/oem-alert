"""
Utility functions and helpers
"""
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text.strip())
    
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    return text

def extract_version_numbers(text: str) -> List[str]:
    """Extract version numbers from text"""
    version_patterns = [
        r'\d+\.\d+(?:\.\d+)?(?:\.\d+)?',
        r'v\d+\.\d+(?:\.\d+)?',
        r'version\s+\d+\.\d+(?:\.\d+)?',
    ]
    
    versions = []
    for pattern in version_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        versions.extend(matches)
    
    return list(set(versions))

def parse_cvss_score(text: str) -> Optional[float]:
    """Parse CVSS score from text"""
    patterns = [
        r'CVSS:3\.\d/(\d+\.\d+)',
        r'CVSS\s+Score:\s*(\d+\.\d+)',
        r'Score:\s*(\d+\.\d+)',
        r'(\d+\.\d+)\s*CVSS',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue
    
    return None

def normalize_product_name(product_name: str) -> str:
    """Normalize product names for consistency"""
    if not product_name:
        return "Unknown Product"
    
    normalizations = {
        'windows': 'Windows',
        'office': 'Office',
        'azure': 'Azure',
        'exchange': 'Exchange',
        'sharepoint': 'SharePoint',
        'sql server': 'SQL Server',
        'visual studio': 'Visual Studio',
        'internet explorer': 'Internet Explorer',
        'edge': 'Edge',
        'outlook': 'Outlook',
        'word': 'Word',
        'excel': 'Excel',
        'powerpoint': 'PowerPoint',
        'teams': 'Teams',
        'onedrive': 'OneDrive',
        'dynamics': 'Dynamics',
        'power bi': 'Power BI',
        'ios': 'iOS',
        'ios xe': 'iOS XE',
        'ios xr': 'iOS XR',
        'nx-os': 'NX-OS',
        'asa': 'ASA',
        'firepower': 'Firepower',
        'catalyst': 'Catalyst',
        'meraki': 'Meraki',
        'webex': 'Webex',
        'ucs': 'UCS',
        'apic': 'APIC',
        'aci': 'ACI',
        'ise': 'ISE',
        'wlc': 'WLC',
        'prime': 'Prime',
        'dna center': 'DNA Center',
        'sd-wan': 'SD-WAN',
        'umbrella': 'Umbrella',
        'duo': 'Duo',
        'talos': 'Talos',
    }
    
    product_lower = product_name.lower()
    
    for key, value in normalizations.items():
        if key in product_lower:
            return value
    
    return product_name.title()

def extract_affected_versions(description: str) -> Optional[str]:
    """Extract affected versions from vulnerability description"""
    version_patterns = [
        r'versions?\s+([0-9\.\s,\-and]+)',
        r'affected\s+versions?\s+([0-9\.\s,\-and]+)',
        r'vulnerable\s+versions?\s+([0-9\.\s,\-and]+)',
        r'([0-9\.\s,\-and]+)\s+and\s+earlier',
        r'([0-9\.\s,\-and]+)\s+and\s+below',
    ]
    
    for pattern in version_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    
    return None

def create_unique_id_from_text(text: str, oem_name: str) -> str:
    """Create a unique ID from text when CVE is not available"""
    import hashlib
    
    clean_text_str = clean_text(text)[:100]
    hash_obj = hashlib.md5(f"{oem_name}-{clean_text_str}".encode())
    
    return f"{oem_name.upper()}-{hash_obj.hexdigest()[:8]}"

def validate_vulnerability_data(vuln_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean vulnerability data"""
    required_fields = ['unique_id', 'product_name', 'oem_name', 'severity_level', 'vulnerability_description', 'published_date']
    
    for field in required_fields:
        if field not in vuln_data or not vuln_data[field]:
            logger.warning(f"Missing required field: {field}")
            if field == 'unique_id':
                vuln_data[field] = create_unique_id_from_text(
                    vuln_data.get('vulnerability_description', ''),
                    vuln_data.get('oem_name', 'Unknown')
                )
            elif field == 'published_date':
                vuln_data[field] = datetime.now()
    
    text_fields = ['product_name', 'vulnerability_description', 'mitigation_strategy']
    for field in text_fields:
        if field in vuln_data and vuln_data[field]:
            vuln_data[field] = clean_text(vuln_data[field])
    
    if 'product_name' in vuln_data:
        vuln_data['product_name'] = normalize_product_name(vuln_data['product_name'])
    
    if 'affected_versions' not in vuln_data or not vuln_data['affected_versions']:
        description = vuln_data.get('vulnerability_description', '')
        affected_versions = extract_affected_versions(description)
        if affected_versions:
            vuln_data['affected_versions'] = affected_versions
    
    return vuln_data

def format_datetime_for_display(dt: datetime) -> str:
    """Format datetime for display"""
    if not dt:
        return "Unknown"
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_date_for_display(dt: datetime) -> str:
    """Format date for display"""
    if not dt:
        return "Unknown"
    
    return dt.strftime('%Y-%m-%d')

def parse_date_range(date_range_str: str) -> Optional[tuple]:
    """Parse date range string and return start/end dates"""
    if not date_range_str:
        return None
    
    try:
        if date_range_str == "7 days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
        elif date_range_str == "30 days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
        elif date_range_str == "90 days":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
        elif date_range_str == "1 year":
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
        else:
            return None
        
        return (start_date, end_date)
    
    except Exception as e:
        logger.error(f"Error parsing date range: {e}")
        return None

def create_summary_statistics(vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create summary statistics from vulnerability list"""
    if not vulnerabilities:
        return {
            'total': 0,
            'by_severity': {},
            'by_oem': {},
            'by_product': {},
            'recent_count': 0
        }
    
    severity_counts = {}
    for vuln in vulnerabilities:
        severity = vuln.get('severity_level', 'Unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    oem_counts = {}
    for vuln in vulnerabilities:
        oem = vuln.get('oem_name', 'Unknown')
        oem_counts[oem] = oem_counts.get(oem, 0) + 1
    
    product_counts = {}
    for vuln in vulnerabilities:
        product = vuln.get('product_name', 'Unknown')
        product_counts[product] = product_counts.get(product, 0) + 1
    
    recent_cutoff = datetime.now() - timedelta(days=7)
    recent_count = 0
    for vuln in vulnerabilities:
        pub_date = vuln.get('published_date')
        if pub_date and pub_date >= recent_cutoff:
            recent_count += 1
    
    return {
        'total': len(vulnerabilities),
        'by_severity': severity_counts,
        'by_oem': oem_counts,
        'by_product': product_counts,
        'recent_count': recent_count
    }
