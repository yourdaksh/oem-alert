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
        # Only initialize if not already done
        if st.session_state.db_ops is None:
            # Initialize database
            init_database()
            
            # Get database session
            db = next(get_db())
            st.session_state.db_ops = DatabaseOperations(db)
        
        if st.session_state.scraper_manager is None:
            # Initialize scraper manager
            st.session_state.scraper_manager = create_scraper_manager()
        
        if st.session_state.email_service is None:
            # Initialize email service
            st.session_state.email_service = create_email_service(st.session_state.db_ops)
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return False

def main():
    """Main application function with authentication and improved UI"""
    # --- Simplified Modern CSS ---
    st.markdown(
        """
        <style>
        /* Global Styles */
        html, body, [class*="css"] {
            background: #0a0a0a !important;
            color: #ffffff !important;
        }
        
        /* Main Background */
        .main, .stApp, .block-container {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%) !important;
            color: #ffffff !important;
        }
        
        /* Simple Button Styling */
        .stButton>button {
            background: #00d4aa !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
        }
        
        .stButton>button:hover {
            background: #00a8cc !important;
        }
        
        /* Simple Form Styling */
        .stTextInput>div>input {
            background: rgba(20, 20, 20, 0.9) !important;
            color: #ffffff !important;
            border: 1px solid #00d4aa !important;
            border-radius: 4px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- Authentication ---
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # Simple Login Page
        st.markdown(
            """
            <div style='text-align: center; padding: 2rem 0;'>
                <h1 style='color: #00d4aa; font-size: 2rem; margin-bottom: 1rem;'>
                    🚨 OEM VULNERABILITY ALERT PLATFORM
                </h1>
                <p style='color: #a0a0a0; margin-bottom: 2rem;'>
                    Monitor critical vulnerabilities from major IT/OT OEMs
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Simple Login Form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(
                """
                <div style='background: rgba(20, 20, 20, 0.9); border-radius: 10px; padding: 2rem; margin: 2rem 0; border: 1px solid #00d4aa;'>
                    <h2 style='color: #00d4aa; text-align: center; margin-bottom: 2rem;'>SECURE ACCESS</h2>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "👤 Username", 
                    value="", 
                    key="login_user",
                    placeholder="Enter your username"
                )
                password = st.text_input(
                    "🔒 Password", 
                    type="password", 
                    value="", 
                    key="login_pass",
                    placeholder="Enter your password"
                )
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    submitted = st.form_submit_button(
                        "🚀 ACCESS PLATFORM", 
                        type="primary",
                        use_container_width=True
                    )
                
                if submitted:
                    # Simple hardcoded credentials (replace with secure method in production)
                    if username == "admin" and password == "admin123":
                        st.session_state.authenticated = True
                        st.success("🎉 Login successful! Initializing platform...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password. Please try again.")
        
        # Footer with additional info
        st.markdown(
            """
            <div style='text-align: center; margin-top: 3rem; padding: 2rem; 
                        background: rgba(20, 20, 20, 0.5); border-radius: 20px; 
                        border: 1px solid rgba(59, 130, 246, 0.2);'>
                <div style='color: #a0a0a0; font-size: 0.9rem;'>
                    🔐 Secure • 🚀 Fast • 📊 Comprehensive • 🎯 Real-time
                </div>
                <div style='color: #666; font-size: 0.8rem; margin-top: 1rem;'>
                    Default credentials: admin / admin123
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.stop()

    # --- Main App Content with Creative Header ---
    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0; margin-bottom: 2rem;'>
            <div style='font-size: 3rem; margin-bottom: 1rem; text-shadow: 0 0 20px rgba(0, 212, 170, 0.5);'>🚨</div>
            <h1 style='color: #00d4aa; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; 
                       text-shadow: 0 0 20px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                OEM VULNERABILITY ALERT PLATFORM
            </h1>
            <div style='color: #a0a0a0; font-size: 1.1rem; font-weight: 300;'>
                Monitor critical and high-severity vulnerabilities from major IT/OT hardware and software OEMs
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Initialize services
    if not initialize_services():
        st.stop()

    # Enhanced Sidebar navigation
    st.sidebar.markdown(
        """
        <div style='text-align: center; padding: 1rem 0; margin-bottom: 2rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem; text-shadow: 0 0 15px rgba(0, 212, 170, 0.5);'>🎯</div>
            <h2 style='color: #00d4aa; font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; 
                       text-shadow: 0 0 10px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                CONTROL CENTER
            </h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown(
        """
        <div style='background: rgba(0, 212, 170, 0.1); border-radius: 12px; padding: 1rem; margin-bottom: 2rem; 
                    border: 1px solid rgba(0, 212, 170, 0.3);'>
            <div style='color: #00d4aa; font-weight: 600; text-align: center;'>
                👋 Welcome, Admin!
            </div>
            <div style='color: #a0a0a0; font-size: 0.9rem; text-align: center; margin-top: 0.5rem;'>
                System Status: <span style='color: #00d4aa;'>🟢 OPERATIONAL</span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    page = st.sidebar.selectbox(
        "🚀 Navigation Menu",
        ["Dashboard", "Vulnerabilities", "Email Subscriptions", "Manual Scan", "Analytics", "Export Data", "Settings"],
        format_func=lambda x: {
            "Dashboard": "📊 Dashboard",
            "Vulnerabilities": "🔍 Vulnerabilities", 
            "Email Subscriptions": "📧 Email Subscriptions",
            "Manual Scan": "🔬 Manual Scan",
            "Analytics": "📈 Analytics",
            "Export Data": "📤 Export Data",
            "Settings": "⚙️ Settings"
        }[x]
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
    elif page == "Export Data":
        show_export_data()
    elif page == "Settings":
        show_settings()

def show_dashboard():
    """Show main dashboard with creative overview"""
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h2 style='color: #00d4aa; font-size: 2rem; font-weight: 600; margin-bottom: 1rem; 
                       text-shadow: 0 0 15px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                📊 DASHBOARD OVERVIEW
            </h2>
            <div style='color: #a0a0a0; font-size: 1rem; font-weight: 300;'>
                Real-time vulnerability monitoring and threat intelligence
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Get statistics
    stats = st.session_state.db_ops.get_vulnerability_stats()
    scan_stats = st.session_state.db_ops.get_scan_stats()
    notification_stats = st.session_state.db_ops.get_notification_stats()
    
    # Enhanced Key metrics with creative styling
    st.markdown(
        """
        <div style='margin-bottom: 2rem;'>
            <h3 style='color: #00d4aa; font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; 
                       text-shadow: 0 0 10px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                🎯 KEY METRICS
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(50, 50, 50, 0.8) 100%); 
                        border-radius: 20px; padding: 2rem; text-align: center; 
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(255, 99, 71, 0.2);
                        border: 2px solid rgba(255, 99, 71, 0.3); backdrop-filter: blur(20px);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #ff6347; 
                           text-shadow: 0 0 10px rgba(255, 99, 71, 0.5); font-family: "JetBrains Mono", monospace;'>
                    {stats['total_vulnerabilities']}
                </div>
                <div style='color: #a0a0a0; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 1px; margin-bottom: 0.5rem;'>Total Vulnerabilities</div>
                <div style='color: #ff6347; font-size: 0.8rem;'>+{stats['recent_vulnerabilities']} (30 days)</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(50, 50, 50, 0.8) 100%); 
                        border-radius: 20px; padding: 2rem; text-align: center; 
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(255, 193, 7, 0.2);
                        border: 2px solid rgba(255, 193, 7, 0.3); backdrop-filter: blur(20px);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #ffc107; 
                           text-shadow: 0 0 10px rgba(255, 193, 7, 0.5); font-family: "JetBrains Mono", monospace;'>
                    {stats['recent_vulnerabilities']}
                </div>
                <div style='color: #a0a0a0; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 1px; margin-bottom: 0.5rem;'>Recent Vulnerabilities</div>
                <div style='color: #ffc107; font-size: 0.8rem;'>Last 30 days</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(50, 50, 50, 0.8) 100%); 
                        border-radius: 20px; padding: 2rem; text-align: center; 
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(0, 212, 170, 0.2);
                        border: 2px solid rgba(0, 212, 170, 0.3); backdrop-filter: blur(20px);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #00d4aa; 
                           text-shadow: 0 0 10px rgba(0, 212, 170, 0.5); font-family: "JetBrains Mono", monospace;'>
                    {scan_stats['success_rate']:.1f}%
                </div>
                <div style='color: #a0a0a0; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 1px; margin-bottom: 0.5rem;'>Scan Success Rate</div>
                <div style='color: #00d4aa; font-size: 0.8rem;'>{scan_stats['successful_scans']}/{scan_stats['total_scans']}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, rgba(30, 30, 30, 0.9) 0%, rgba(50, 50, 50, 0.8) 100%); 
                        border-radius: 20px; padding: 2rem; text-align: center; 
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(138, 43, 226, 0.2);
                        border: 2px solid rgba(138, 43, 226, 0.3); backdrop-filter: blur(20px);'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #8a2be2; 
                           text-shadow: 0 0 10px rgba(138, 43, 226, 0.5); font-family: "JetBrains Mono", monospace;'>
                    {notification_stats['total_notifications']}
                </div>
                <div style='color: #a0a0a0; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 1px; margin-bottom: 0.5rem;'>Email Notifications</div>
                <div style='color: #8a2be2; font-size: 0.8rem;'>{notification_stats['success_rate']:.1f}% success rate</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Enhanced Recent vulnerabilities section
    st.markdown(
        """
        <div style='margin: 3rem 0 2rem 0;'>
            <h3 style='color: #00d4aa; font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; 
                       text-shadow: 0 0 10px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                🔍 RECENT CRITICAL & HIGH SEVERITY VULNERABILITIES
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
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
        # Create a more visually appealing display
        for i, vuln in enumerate(all_recent[:5]):  # Show top 5
            severity_color = {
                'Critical': '#ff3b30',
                'High': '#ff9500', 
                'Medium': '#ffc107',
                'Low': '#34c759'
            }.get(vuln.severity_level, '#8e8e93')
            
            severity_icon = {
                'Critical': '🚨',
                'High': '⚠️',
                'Medium': '⚡',
                'Low': 'ℹ️'
            }.get(vuln.severity_level, '❓')
            
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, rgba(20, 20, 20, 0.95) 0%, rgba(30, 30, 30, 0.9) 100%); 
                            border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; 
                            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px {severity_color}20;
                            border: 2px solid {severity_color}40; backdrop-filter: blur(20px);'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <div style='display: flex; align-items: center; gap: 1rem;'>
                            <div style='font-size: 1.5rem;'>{severity_icon}</div>
                            <div>
                                <div style='color: {severity_color}; font-weight: 600; font-size: 1.1rem; 
                                           text-shadow: 0 0 10px {severity_color}50;'>
                                    {vuln.severity_level} - {vuln.unique_id}
                                </div>
                                <div style='color: #a0a0a0; font-size: 0.9rem;'>{vuln.oem_name}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: #00d4aa; font-weight: 600; font-family: "JetBrains Mono", monospace;'>
                                {vuln.cvss_score or 'N/A'}
                            </div>
                            <div style='color: #a0a0a0; font-size: 0.8rem;'>CVSS</div>
                        </div>
                    </div>
                    <div style='color: #ffffff; font-weight: 500; margin-bottom: 0.5rem;'>
                        {vuln.product_name}
                    </div>
                    <div style='color: #a0a0a0; font-size: 0.9rem;'>
                        Published: {vuln.published_date.strftime('%Y-%m-%d')}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Show remaining vulnerabilities in a compact table
        if len(all_recent) > 5:
            st.markdown(
                """
                <div style='margin-top: 2rem;'>
                    <h4 style='color: #00d4aa; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; 
                               text-shadow: 0 0 10px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                        📋 ADDITIONAL VULNERABILITIES
                    </h4>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            df_recent = pd.DataFrame([{
                'Unique ID': vuln.unique_id,
                'Product': vuln.product_name,
                'OEM': vuln.oem_name,
                'Severity': vuln.severity_level,
                'Published': vuln.published_date.strftime('%Y-%m-%d'),
                'CVSS': vuln.cvss_score or 'N/A'
            } for vuln in all_recent[5:10]])
            
            st.dataframe(df_recent, use_container_width=True)
    else:
        st.markdown(
            """
            <div style='background: rgba(20, 20, 20, 0.5); border-radius: 16px; padding: 2rem; text-align: center; 
                        border: 2px solid rgba(0, 212, 170, 0.3);'>
                <div style='font-size: 2rem; margin-bottom: 1rem; color: #00d4aa;'>✅</div>
                <div style='color: #00d4aa; font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem;'>
                    No Recent Critical or High Severity Vulnerabilities
                </div>
                <div style='color: #a0a0a0; font-size: 0.9rem;'>
                    All systems are secure! No new critical or high-severity vulnerabilities found in the last 7 days.
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Enhanced OEM Status section
    st.markdown(
        """
        <div style='margin: 3rem 0 2rem 0;'>
            <h3 style='color: #00d4aa; font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; 
                       text-shadow: 0 0 10px rgba(0, 212, 170, 0.3); font-family: "Space Grotesk", sans-serif;'>
                🏢 OEM SCANNER STATUS
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    scraper_status = st.session_state.scraper_manager.get_scraper_status()
    
    # Create a grid of OEM status cards
    cols = st.columns(3)
    for i, (oem_id, status) in enumerate(scraper_status.items()):
        with cols[i % 3]:
            is_enabled = status['enabled']
            status_color = '#00d4aa' if is_enabled else '#ff3b30'
            status_icon = '🟢' if is_enabled else '🔴'
            status_text = 'ACTIVE' if is_enabled else 'DISABLED'
            
            last_scan = scan_stats['last_scans_by_oem'].get(oem_id, 'Never')
            
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, rgba(20, 20, 20, 0.95) 0%, rgba(30, 30, 30, 0.9) 100%); 
                            border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; 
                            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px {status_color}20;
                            border: 2px solid {status_color}40; backdrop-filter: blur(20px);'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <div style='font-size: 1.5rem;'>{status_icon}</div>
                        <div style='color: {status_color}; font-weight: 600; font-size: 0.8rem; 
                                   text-transform: uppercase; letter-spacing: 1px;'>
                            {status_text}
                        </div>
                    </div>
                    <div style='color: #ffffff; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>
                        {status['name']}
                    </div>
                    <div style='color: #a0a0a0; font-size: 0.9rem; margin-bottom: 0.5rem;'>
                        {status['description']}
                    </div>
                    <div style='display: flex; justify-content: space-between; margin-top: 1rem;'>
                        <div>
                            <div style='color: #00d4aa; font-size: 0.8rem; font-weight: 600;'>SCAN INTERVAL</div>
                            <div style='color: #a0a0a0; font-size: 0.9rem;'>{status['scan_interval_hours']}h</div>
                        </div>
                        <div>
                            <div style='color: #00d4aa; font-size: 0.8rem; font-weight: 600;'>LAST SCAN</div>
                            <div style='color: #a0a0a0; font-size: 0.9rem;'>{last_scan}</div>
                        </div>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )

def show_vulnerabilities():
    """Show vulnerabilities with enhanced filtering options"""
    st.header("🔍 Vulnerability Browser")
    
    # Enhanced filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        oem_filter = st.selectbox(
            "Filter by OEM",
            ["All"] + list(st.session_state.db_ops.get_vulnerability_stats()['oem_distribution'].keys())
        )
    
    with col2:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["Critical", "High", "Medium", "Low"],
            default=["Critical", "High"]
        )
    
    with col3:
        days_back = st.selectbox(
            "Time Range",
            ["All", "7 days", "30 days", "90 days", "1 year"]
        )
    
    with col4:
        search_term = st.text_input("Search (CVE, Product, Description)")
    
    # Additional filters
    col5, col6, col7 = st.columns(3)
    
    with col5:
        cvss_min = st.slider("Minimum CVSS Score", 0.0, 10.0, 0.0, 0.1)
    
    with col6:
        sort_by = st.selectbox(
            "Sort by",
            ["Published Date (Newest)", "Published Date (Oldest)", "CVSS Score (High to Low)", "CVSS Score (Low to High)", "Severity"]
        )
    
    with col7:
        limit = st.selectbox(
            "Results per page",
            [25, 50, 100, 200, 500]
        )
    
    # Convert filters
    oem_name = None if oem_filter == "All" else oem_filter
    days = None
    if days_back != "All":
        days = int(days_back.split()[0])
    
    # Get vulnerabilities
    if search_term:
        vulnerabilities = st.session_state.db_ops.search_vulnerabilities(search_term, limit=limit)
    else:
        vulnerabilities = st.session_state.db_ops.get_vulnerabilities(
            oem_name=oem_name,
            severity=None,  # We'll filter by severity after getting results
            days_back=days,
            limit=limit * 2  # Get more to filter by severity
        )
    
    # Apply severity filter
    if severity_filter:
        vulnerabilities = [v for v in vulnerabilities if v.severity_level in severity_filter]
    
    # Apply CVSS filter
    if cvss_min > 0:
        vulnerabilities = [v for v in vulnerabilities if v.cvss_score and float(v.cvss_score) >= cvss_min]
    
    # Apply sorting
    if sort_by == "Published Date (Newest)":
        vulnerabilities.sort(key=lambda x: x.published_date, reverse=True)
    elif sort_by == "Published Date (Oldest)":
        vulnerabilities.sort(key=lambda x: x.published_date, reverse=False)
    elif sort_by == "CVSS Score (High to Low)":
        vulnerabilities.sort(key=lambda x: float(x.cvss_score) if x.cvss_score else 0, reverse=True)
    elif sort_by == "CVSS Score (Low to High)":
        vulnerabilities.sort(key=lambda x: float(x.cvss_score) if x.cvss_score else 0, reverse=False)
    elif sort_by == "Severity":
        severity_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "Unknown": 0}
        vulnerabilities.sort(key=lambda x: severity_order.get(x.severity_level, 0), reverse=True)
    
    # Limit results
    vulnerabilities = vulnerabilities[:limit]
    
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

def show_export_data():
    """Show data export functionality"""
    st.header("📤 Export Data")
    
    st.subheader("Export Vulnerabilities")
    
    # Export filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_oem = st.selectbox(
            "Filter by OEM",
            ["All"] + list(st.session_state.db_ops.get_vulnerability_stats()['oem_distribution'].keys()),
            key="export_oem"
        )
    
    with col2:
        export_severity = st.selectbox(
            "Filter by Severity",
            ["All", "Critical", "High", "Medium", "Low"],
            key="export_severity"
        )
    
    with col3:
        export_days = st.selectbox(
            "Time Range",
            ["All", "7 days", "30 days", "90 days", "1 year"],
            key="export_days"
        )
    
    # Convert filters
    oem_name = None if export_oem == "All" else export_oem
    severity = None if export_severity == "All" else export_severity
    days = None
    if export_days != "All":
        days = int(export_days.split()[0])
    
    # Get vulnerabilities for export
    vulnerabilities = st.session_state.db_ops.get_vulnerabilities(
        oem_name=oem_name,
        severity=severity,
        days_back=days,
        limit=10000  # Large limit for export
    )
    
    st.info(f"Found {len(vulnerabilities)} vulnerabilities matching your criteria.")
    
    if vulnerabilities:
        # Create DataFrame for export
        df_export = pd.DataFrame([{
            'Unique ID': vuln.unique_id,
            'Product': vuln.product_name,
            'Version': vuln.product_version or 'N/A',
            'OEM': vuln.oem_name,
            'Severity': vuln.severity_level,
            'CVSS': vuln.cvss_score or 'N/A',
            'Published Date': vuln.published_date.strftime('%Y-%m-%d'),
            'Discovered Date': vuln.discovered_date.strftime('%Y-%m-%d'),
            'Description': vuln.vulnerability_description,
            'Source URL': vuln.source_url
        } for vuln in vulnerabilities])
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col2:
            # JSON Export
            json_data = df_export.to_json(orient='records', indent=2)
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col3:
            # Excel Export
            try:
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Vulnerabilities', index=False)
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.warning("Excel export requires openpyxl. Install with: pip install openpyxl")
        
        # Preview data
        st.subheader("Data Preview")
        st.dataframe(df_export.head(10), use_container_width=True)
    
    # Export subscriptions
    st.subheader("Export Email Subscriptions")
    
    subscriptions = st.session_state.db_ops.get_subscriptions()
    
    if subscriptions:
        df_subs = pd.DataFrame([{
            'ID': sub.id,
            'Email': sub.email,
            'OEM': sub.oem_name or 'All',
            'Product': sub.product_name or 'All',
            'Severity Filter': sub.severity_filter,
            'Active': sub.is_active,
            'Created Date': sub.created_date.strftime('%Y-%m-%d')
        } for sub in subscriptions])
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_subs = df_subs.to_csv(index=False)
            st.download_button(
                label="📄 Download Subscriptions CSV",
                data=csv_subs,
                file_name=f"subscriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_subs = df_subs.to_json(orient='records', indent=2)
            st.download_button(
                label="📋 Download Subscriptions JSON",
                data=json_subs,
                file_name=f"subscriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("No subscriptions found.")

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
