"""
Main Streamlit application for OEM Vulnerability Alert Platform
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

# Import our modules
from database import get_db, init_database
from database.operations import DatabaseOperations
from database.models import Vulnerability, Subscription, ScanLog
from scrapers import create_scraper_manager
from email_notifications import create_email_service
from config import get_all_oems, get_enabled_oems

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="OEM Vulnerability Alert Platform",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_ops' not in st.session_state:
    st.session_state.db_ops = None
if 'scraper_manager' not in st.session_state:
    st.session_state.scraper_manager = None
if 'email_service' not in st.session_state:
    st.session_state.email_service = None

def initialize_services():
    """Initialize database and services"""
    try:
        # Initialize database
        init_database()
        
        # Get database session
        db = next(get_db())
        st.session_state.db_ops = DatabaseOperations(db)
        
        # Initialize scraper manager
        st.session_state.scraper_manager = create_scraper_manager()
        
        # Initialize email service
        st.session_state.email_service = create_email_service(st.session_state.db_ops)
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return False

def main():
    """Main application function"""
    st.title("🚨 OEM Vulnerability Alert Platform")
    st.markdown("Monitor critical and high-severity vulnerabilities from major IT/OT hardware and software OEMs")
    
    # Initialize services
    if not initialize_services():
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Dashboard", "Vulnerabilities", "Email Subscriptions", "Manual Scan", "Analytics", "Settings"]
    )
    
    # Route to appropriate page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Vulnerabilities":
        show_vulnerabilities()
    elif page == "Email Subscriptions":
        show_subscriptions()
    elif page == "Manual Scan":
        show_manual_scan()
    elif page == "Analytics":
        show_analytics()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    """Show main dashboard with overview"""
    st.header("📊 Dashboard Overview")
    
    # Get statistics
    stats = st.session_state.db_ops.get_vulnerability_stats()
    scan_stats = st.session_state.db_ops.get_scan_stats()
    notification_stats = st.session_state.db_ops.get_notification_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Vulnerabilities",
            value=stats['total_vulnerabilities'],
            delta=f"+{stats['recent_vulnerabilities']} (30 days)"
        )
    
    with col2:
        st.metric(
            label="Recent Vulnerabilities",
            value=stats['recent_vulnerabilities'],
            delta="Last 30 days"
        )
    
    with col3:
        st.metric(
            label="Scan Success Rate",
            value=f"{scan_stats['success_rate']:.1f}%",
            delta=f"{scan_stats['successful_scans']}/{scan_stats['total_scans']}"
        )
    
    with col4:
        st.metric(
            label="Email Notifications",
            value=notification_stats['total_notifications'],
            delta=f"{notification_stats['success_rate']:.1f}% success rate"
        )
    
    # Recent vulnerabilities
    st.subheader("🔍 Recent Critical & High Severity Vulnerabilities")
    recent_vulns = st.session_state.db_ops.get_vulnerabilities(
        severity="Critical",
        days_back=7,
        limit=10
    )
    
    # Also get High severity
    high_vulns = st.session_state.db_ops.get_vulnerabilities(
        severity="High",
        days_back=7,
        limit=10
    )
    
    all_recent = recent_vulns + high_vulns
    all_recent.sort(key=lambda x: x.published_date, reverse=True)
    
    if all_recent:
        df_recent = pd.DataFrame([{
            'Unique ID': vuln.unique_id,
            'Product': vuln.product_name,
            'OEM': vuln.oem_name,
            'Severity': vuln.severity_level,
            'Published': vuln.published_date.strftime('%Y-%m-%d'),
            'CVSS': vuln.cvss_score or 'N/A'
        } for vuln in all_recent[:10]])
        
        st.dataframe(df_recent, use_container_width=True)
    else:
        st.info("No recent critical or high severity vulnerabilities found.")
    
    # OEM Status
    st.subheader("🏢 OEM Scanner Status")
    scraper_status = st.session_state.scraper_manager.get_scraper_status()
    
    status_df = pd.DataFrame([
        {
            'OEM': status['name'],
            'Status': '✅ Enabled' if status['enabled'] else '❌ Disabled',
            'Scan Interval': f"{status['scan_interval_hours']}h",
            'Last Scan': scan_stats['last_scans_by_oem'].get(oem_id, 'Never')
        }
        for oem_id, status in scraper_status.items()
    ])
    
    st.dataframe(status_df, use_container_width=True)

def show_vulnerabilities():
    """Show vulnerabilities with filtering options"""
    st.header("🔍 Vulnerability Browser")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        oem_filter = st.selectbox(
            "Filter by OEM",
            ["All"] + list(st.session_state.db_ops.get_vulnerability_stats()['oem_distribution'].keys())
        )
    
    with col2:
        severity_filter = st.selectbox(
            "Filter by Severity",
            ["All", "Critical", "High", "Medium", "Low"]
        )
    
    with col3:
        days_back = st.selectbox(
            "Time Range",
            ["All", "7 days", "30 days", "90 days", "1 year"]
        )
    
    with col4:
        search_term = st.text_input("Search (CVE, Product, Description)")
    
    # Convert filters
    oem_name = None if oem_filter == "All" else oem_filter
    severity = None if severity_filter == "All" else severity_filter
    days = None
    if days_back != "All":
        days = int(days_back.split()[0])
    
    # Get vulnerabilities
    if search_term:
        vulnerabilities = st.session_state.db_ops.search_vulnerabilities(search_term)
    else:
        vulnerabilities = st.session_state.db_ops.get_vulnerabilities(
            oem_name=oem_name,
            severity=severity,
            days_back=days,
            limit=100
        )
    
    # Display results
    st.subheader(f"Found {len(vulnerabilities)} vulnerabilities")
    
    if vulnerabilities:
        # Create DataFrame
        df = pd.DataFrame([{
            'Unique ID': vuln.unique_id,
            'Product': vuln.product_name,
            'Version': vuln.product_version or 'N/A',
            'OEM': vuln.oem_name,
            'Severity': vuln.severity_level,
            'CVSS': vuln.cvss_score or 'N/A',
            'Published': vuln.published_date.strftime('%Y-%m-%d'),
            'Description': vuln.vulnerability_description[:100] + "..." if len(vuln.vulnerability_description) > 100 else vuln.vulnerability_description,
            'Source URL': vuln.source_url
        } for vuln in vulnerabilities])
        
        # Display with expandable rows
        for idx, row in df.iterrows():
            with st.expander(f"{row['Severity']} - {row['Unique ID']} - {row['Product']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**OEM:** {row['OEM']}")
                    st.write(f"**Product:** {row['Product']}")
                    st.write(f"**Version:** {row['Version']}")
                    st.write(f"**CVSS Score:** {row['CVSS']}")
                
                with col2:
                    st.write(f"**Severity:** {row['Severity']}")
                    st.write(f"**Published:** {row['Published']}")
                    st.write(f"**Unique ID:** {row['Unique ID']}")
                
                st.write(f"**Description:** {row['Description']}")
                
                if row['Source URL']:
                    st.write(f"**Source:** [View Details]({row['Source URL']})")
    else:
        st.info("No vulnerabilities found matching your criteria.")

def show_subscriptions():
    """Show email subscription management"""
    st.header("📧 Email Subscription Management")
    
    # Add new subscription
    st.subheader("Add New Subscription")
    
    with st.form("add_subscription"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email Address")
            oem_name = st.selectbox(
                "OEM (leave blank for all)",
                ["All"] + list(st.session_state.db_ops.get_vulnerability_stats()['oem_distribution'].keys())
            )
        
        with col2:
            product_name = st.text_input("Product Name (optional)")
            severity_filter = st.multiselect(
                "Severity Levels",
                ["Critical", "High", "Medium", "Low"],
                default=["Critical", "High"]
            )
        
        submitted = st.form_submit_button("Add Subscription")
        
        if submitted:
            if email and severity_filter:
                oem = None if oem_name == "All" else oem_name
                severity_str = ",".join(severity_filter)
                
                try:
                    subscription = st.session_state.db_ops.add_subscription(
                        email=email,
                        oem_name=oem,
                        product_name=product_name if product_name else None,
                        severity_filter=severity_str
                    )
                    st.success(f"Subscription added successfully! ID: {subscription.id}")
                except Exception as e:
                    st.error(f"Failed to add subscription: {e}")
            else:
                st.error("Please provide email and select at least one severity level.")
    
    # Manage existing subscriptions
    st.subheader("Manage Existing Subscriptions")
    
    subscriptions = st.session_state.db_ops.get_subscriptions()
    
    if subscriptions:
        df_subs = pd.DataFrame([{
            'ID': sub.id,
            'Email': sub.email,
            'OEM': sub.oem_name or 'All',
            'Product': sub.product_name or 'All',
            'Severity': sub.severity_filter,
            'Active': sub.is_active,
            'Created': sub.created_date.strftime('%Y-%m-%d')
        } for sub in subscriptions])
        
        st.dataframe(df_subs, use_container_width=True)
        
        # Delete subscription
        st.subheader("Delete Subscription")
        sub_id = st.number_input("Subscription ID to delete", min_value=1)
        
        if st.button("Delete Subscription"):
            try:
                success = st.session_state.db_ops.delete_subscription(sub_id)
                if success:
                    st.success("Subscription deleted successfully!")
                    st.rerun()
                else:
                    st.error("Subscription not found.")
            except Exception as e:
                st.error(f"Failed to delete subscription: {e}")
    else:
        st.info("No subscriptions found.")

def show_manual_scan():
    """Show manual scanning interface"""
    st.header("🔍 Manual Vulnerability Scan")
    
    st.subheader("Scan All OEMs")
    
    if st.button("🚀 Run Full Scan", type="primary"):
        with st.spinner("Scanning all OEMs for vulnerabilities..."):
            try:
                results = st.session_state.scraper_manager.run_all_scrapers()
                
                total_found = 0
                total_new = 0
                
                for oem_id, vulnerabilities in results.items():
                    st.write(f"**{oem_id.title()}:** {len(vulnerabilities)} vulnerabilities found")
                    
                    # Add vulnerabilities to database
                    for vuln_data in vulnerabilities:
                        try:
                            vuln = st.session_state.db_ops.add_vulnerability(vuln_data)
                            total_found += 1
                            
                            # Check if this is a new vulnerability
                            if vuln.discovered_date == vuln.published_date:
                                total_new += 1
                                
                                # Send email notifications
                                notification_results = st.session_state.email_service.send_bulk_vulnerability_alerts(vuln)
                                st.write(f"  - Sent {notification_results['sent']} email notifications")
                                
                        except Exception as e:
                            logger.error(f"Error adding vulnerability: {e}")
                
                st.success(f"Scan completed! Found {total_found} total vulnerabilities, {total_new} new ones.")
                
            except Exception as e:
                st.error(f"Scan failed: {e}")
    
    # Individual OEM scanning
    st.subheader("Scan Individual OEMs")
    
    scraper_status = st.session_state.scraper_manager.get_scraper_status()
    
    for oem_id, status in scraper_status.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{status['name']}** - {status['description']}")
        
        with col2:
            if st.button(f"Scan {status['name']}", key=f"scan_{oem_id}"):
                with st.spinner(f"Scanning {status['name']}..."):
                    try:
                        vulnerabilities = st.session_state.scraper_manager.run_scraper(oem_id)
                        
                        new_count = 0
                        for vuln_data in vulnerabilities:
                            try:
                                vuln = st.session_state.db_ops.add_vulnerability(vuln_data)
                                if vuln.discovered_date == vuln.published_date:
                                    new_count += 1
                                    st.session_state.email_service.send_bulk_vulnerability_alerts(vuln)
                            except Exception as e:
                                logger.error(f"Error adding vulnerability: {e}")
                        
                        st.success(f"Found {len(vulnerabilities)} vulnerabilities, {new_count} new")
                        
                    except Exception as e:
                        st.error(f"Scan failed: {e}")

def show_analytics():
    """Show analytics and charts"""
    st.header("📈 Analytics & Insights")
    
    # Get statistics
    stats = st.session_state.db_ops.get_vulnerability_stats()
    
    # Severity distribution
    st.subheader("Vulnerability Severity Distribution")
    
    if stats['severity_distribution']:
        fig_severity = px.pie(
            values=list(stats['severity_distribution'].values()),
            names=list(stats['severity_distribution'].keys()),
            title="Vulnerabilities by Severity"
        )
        st.plotly_chart(fig_severity, use_container_width=True)
    
    # OEM distribution
    st.subheader("Vulnerabilities by OEM")
    
    if stats['oem_distribution']:
        # Sort by count
        sorted_oems = sorted(stats['oem_distribution'].items(), key=lambda x: x[1], reverse=True)
        
        fig_oem = px.bar(
            x=[item[0] for item in sorted_oems],
            y=[item[1] for item in sorted_oems],
            title="Vulnerabilities by OEM",
            labels={'x': 'OEM', 'y': 'Count'}
        )
        fig_oem.update_xaxes(tickangle=45)
        st.plotly_chart(fig_oem, use_container_width=True)
    
    # Recent trends
    st.subheader("Recent Vulnerability Trends")
    
    # Get vulnerabilities from last 30 days
    recent_vulns = st.session_state.db_ops.get_vulnerabilities(days_back=30, limit=1000)
    
    if recent_vulns:
        # Group by date
        vuln_dates = [vuln.published_date.date() for vuln in recent_vulns]
        date_counts = pd.Series(vuln_dates).value_counts().sort_index()
        
        fig_trend = px.line(
            x=date_counts.index,
            y=date_counts.values,
            title="Vulnerabilities Published Over Time (Last 30 Days)",
            labels={'x': 'Date', 'y': 'Count'}
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Scan statistics
    st.subheader("Scanner Performance")
    
    scan_stats = st.session_state.db_ops.get_scan_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Scans", scan_stats['total_scans'])
        st.metric("Successful Scans", scan_stats['successful_scans'])
    
    with col2:
        st.metric("Failed Scans", scan_stats['error_scans'])
        st.metric("Success Rate", f"{scan_stats['success_rate']:.1f}%")

def show_settings():
    """Show settings and configuration"""
    st.header("⚙️ Settings & Configuration")
    
    # Email configuration
    st.subheader("Email Configuration")
    
    if st.button("Test Email Configuration"):
        with st.spinner("Testing email configuration..."):
            success = st.session_state.email_service.test_email_configuration()
            if success:
                st.success("Email configuration test successful!")
            else:
                st.error("Email configuration test failed. Check your SMTP settings.")
    
    # Database information
    st.subheader("Database Information")
    
    stats = st.session_state.db_ops.get_vulnerability_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Vulnerabilities", stats['total_vulnerabilities'])
    
    with col2:
        st.metric("Recent Vulnerabilities", stats['recent_vulnerabilities'])
    
    with col3:
        subscriptions = st.session_state.db_ops.get_subscriptions()
        st.metric("Active Subscriptions", len(subscriptions))
    
    # OEM configuration
    st.subheader("OEM Configuration")
    
    oems_config = get_all_oems()
    
    for oem_id, config in oems_config.items():
        with st.expander(f"{config['name']} - {config['description']}"):
            st.write(f"**Base URL:** {config['base_url']}")
            st.write(f"**Vulnerability URL:** {config['vulnerability_url']}")
            st.write(f"**RSS URL:** {config['rss_url']}")
            st.write(f"**Scan Interval:** {config['scan_interval_hours']} hours")
            st.write(f"**Status:** {'Enabled' if config['enabled'] else 'Disabled'}")
    
    # System information
    st.subheader("System Information")
    
    st.write(f"**Application Version:** 1.0.0")
    st.write(f"**Database:** SQLite")
    st.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
