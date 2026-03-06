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
from slack_notifications import create_slack_service
from config import get_all_oems, get_enabled_oems
from utils.supabase_client import authenticate_user, is_supabase_enabled, sign_up_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Vulnerability Scrapper",
    page_icon="🔒",
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
if 'slack_service' not in st.session_state:
    st.session_state.slack_service = None
if 'supabase_session' not in st.session_state:
    st.session_state.supabase_session = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

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
        
        if st.session_state.slack_service is None:
            # Initialize Slack service
            st.session_state.slack_service = create_slack_service(st.session_state.db_ops)
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return False

def main():
    """Main application function with authentication and improved UI"""

    st.markdown(
        """
        <style>
        /* Global Dark Theme - Pitch Black with Red & Neon Green */
        html, body, [class*="css"] {
            background: #000000 !important;
            color: #ffffff !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }
        
        /* Main Background */
        .main, .stApp, .block-container {
            background: #000000 !important;
            color: #ffffff !important;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: #0a0a0a !important;
            border-right: 1px solid #1a1a1a !important;
        }
        
        /* Button Styling - Neon Green */
        .stButton>button {
            background: linear-gradient(135deg, #00ff41 0%, #00cc33 100%) !important;
            color: #000000 !important;
            border-radius: 8px !important;
            border: 1px solid #00ff41 !important;
            padding: 0.625rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 0 15px rgba(0, 255, 65, 0.4), 0 4px 6px rgba(0, 0, 0, 0.3) !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }
        
        .stButton>button:hover {
            background: linear-gradient(135deg, #00ff41 0%, #00ff66 100%) !important;
            box-shadow: 0 0 25px rgba(0, 255, 65, 0.6), 0 6px 12px rgba(0, 0, 0, 0.4) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Button Text and Labels */
        .stButton>button * {
            color: #000000 !important;
        }
        
        .stButton label {
            color: #ffffff !important;
        }
        
        /* Text under buttons */
        .stButton + p,
        .stButton + div,
        .stButton ~ p,
        .stButton ~ div {
            color: #ffffff !important;
        }
        
        /* All text elements near buttons */
        [data-testid="stButton"] + *,
        [data-testid="stButton"] ~ * {
            color: #ffffff !important;
        }
        
        /* Button container text */
        .stButton {
            color: #ffffff !important;
        }
        
        .stButton * {
            color: inherit !important;
        }
        
        /* Ensure button labels are white */
        .element-container:has(.stButton) label,
        .element-container:has(.stButton) p,
        .element-container:has(.stButton) div {
            color: #ffffff !important;
        }
        
        /* Input Field Styling */
        .stTextInput>div>div>input {
            background: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 6px !important;
            padding: 0.5rem 0.75rem !important;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #00ff41 !important;
            box-shadow: 0 0 10px rgba(0, 255, 65, 0.3) !important;
            background: #0f0f0f !important;
        }
        
        /* Selectbox Styling */
        .stSelectbox>div>div>select {
            background: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 6px !important;
        }
        
        /* Success/Error Messages */
        .stSuccess {
            background: rgba(0, 255, 65, 0.15) !important;
            color: #00ff41 !important;
            border-left: 4px solid #00ff41 !important;
            border-radius: 6px !important;
        }
        
        .stError {
            background: rgba(255, 0, 0, 0.15) !important;
            color: #ff3333 !important;
            border-left: 4px solid #ff3333 !important;
            border-radius: 6px !important;
        }
        
        .stInfo {
            background: rgba(0, 255, 65, 0.1) !important;
            color: #00ff41 !important;
            border-left: 4px solid #00ff41 !important;
            border-radius: 6px !important;
        }
        
        /* Dataframe Styling */
        .dataframe {
            background: #0a0a0a !important;
            border: 1px solid #1a1a1a !important;
            border-radius: 8px !important;
            color: #ffffff !important;
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #0a0a0a !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 0.75rem 1.5rem;
            background: #1a1a1a !important;
            color: #ffffff !important;
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: #000000 !important;
            border-bottom: 2px solid #00ff41 !important;
            color: #00ff41 !important;
        }
        
        /* Metric Cards */
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #00ff41 !important;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #ffffff !important;
            font-weight: 700 !important;
            text-shadow: 0 0 10px rgba(0, 255, 65, 0.3) !important;
        }
        
        /* Links */
        a {
            color: #00ff41 !important;
        }
        
        a:hover {
            color: #00ff66 !important;
            text-shadow: 0 0 8px rgba(0, 255, 65, 0.5) !important;
        }
        
        /* Sidebar Text Colors */
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }
        
        [data-testid="stSidebar"] label {
            color: #cccccc !important;
            font-weight: 500 !important;
        }
        
        /* Selectbox Labels */
        label {
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        
        /* Subheader Styling */
        h3, h4, h5, h6 {
            color: #ffffff !important;
        }
        
        /* Paragraph Text */
        p {
            color: #ffffff !important;
        }
        
        /* All text elements */
        div, span, p, label, small {
            color: #ffffff !important;
        }
        
        /* Text that might appear grey */
        .element-container p,
        .element-container div,
        .element-container span {
            color: #ffffff !important;
        }
        
        /* Streamlit write output */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] div,
        [data-testid="stMarkdownContainer"] span {
            color: #ffffff !important;
        }
        
        /* Table/Dataframe Styling */
        table {
            background: #0a0a0a !important;
            color: #ffffff !important;
        }
        
        th {
            background: #1a1a1a !important;
            color: #00ff41 !important;
            font-weight: 600 !important;
            border: 1px solid #333333 !important;
        }
        
        td {
            background: #0a0a0a !important;
            color: #ffffff !important;
            border: 1px solid #1a1a1a !important;
        }
        
        /* Expander Styling */
        .streamlit-expanderHeader {
            color: #ffffff !important;
            font-weight: 600 !important;
            background: #1a1a1a !important;
        }
        
        /* Warning/Info Boxes */
        .stWarning {
            background: rgba(255, 200, 0, 0.15) !important;
            color: #ffcc00 !important;
            border-left: 4px solid #ffcc00 !important;
            border-radius: 6px !important;
        }
        
        /* Slider Styling */
        .stSlider label {
            color: #ffffff !important;
        }
        
        /* Multiselect Styling */
        .stMultiSelect label {
            color: #ffffff !important;
        }
        
        /* Number Input Styling */
        .stNumberInput label {
            color: #ffffff !important;
        }
        
        .stNumberInput input {
            background: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
        }
        
        /* Text Area Styling */
        textarea {
            background: #1a1a1a !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
        }
        
        /* Checkbox Styling */
        .stCheckbox label {
            color: #ffffff !important;
        }
        
        /* Radio Button Styling */
        .stRadio label {
            color: #ffffff !important;
        }
        
        /* Spinner Text */
        .stSpinner > div {
            color: #00ff41 !important;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #000000;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00ff41;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #00ff66;
        }
        
        /* Streamlit markdown containers - ensure white text */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] div:not([style*="color"]),
        [data-testid="stMarkdownContainer"] span:not([style*="color"]) {
            color: #ffffff !important;
        }
        
        /* Text elements that might appear grey */
        .element-container p:not([style*="color"]),
        .element-container div:not([style*="color"]),
        .element-container span:not([style*="color"]) {
            color: #ffffff !important;
        }
        
        /* Text after buttons - ensure white */
        .stButton + * p,
        .stButton ~ * p,
        .stButton + * div:not([style*="color"]),
        .stButton ~ * div:not([style*="color"]) {
            color: #ffffff !important;
        }
        
        /* Streamlit write output */
        [class*="stMarkdown"] p,
        [class*="stMarkdown"] div:not([style*="color"]) {
            color: #ffffff !important;
        }
        
        /* Ensure regular text is white, but preserve styled elements */
        p:not([style*="color"]),
        div:not([style*="color"]):not(.stButton):not([class*="st"]) {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
  
        st.markdown(
            """
            <div style='text-align: center; padding: 3rem 0 2rem 0;'>
                <h1 style='color: #ffffff; font-size: 2.5rem; margin-bottom: 0.75rem; font-weight: 700; letter-spacing: -0.5px; text-shadow: 0 0 20px rgba(0, 255, 65, 0.5);'>
                    Vulnerability Scrapper
                </h1>
                <p style='color: #cccccc; margin-bottom: 2rem; font-size: 1.1rem; font-weight: 400;'>
                    Monitor critical vulnerabilities from major IT/OT OEMs
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        

        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(
                """
                <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 2.5rem; margin: 2rem 0; border: 1px solid #00ff41; box-shadow: 0 0 30px rgba(0, 255, 65, 0.2), 0 4px 6px rgba(0, 0, 0, 0.5);'>
                    <h2 style='color: #00ff41; text-align: center; margin-bottom: 2rem; font-weight: 700; font-size: 1.75rem; text-shadow: 0 0 15px rgba(0, 255, 65, 0.5);'>Secure Access</h2>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Check if Supabase is enabled
            use_supabase_auth = is_supabase_enabled()
            
            if use_supabase_auth:
                # Supabase authentication mode
                tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
                
                with tab1:
                    with st.form("login_form", clear_on_submit=False):
                        email = st.text_input(
                            "Email", 
                            value="", 
                            key="login_email",
                            placeholder="Enter your email"
                        )
                        password = st.text_input(
                            "Password", 
                            type="password", 
                            value="", 
                            key="login_pass",
                            placeholder="Enter your password"
                        )
                        
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                        with col_btn2:
                            submitted = st.form_submit_button(
                                "Sign In", 
                                type="primary",
                                use_container_width=True
                            )
                        
                        if submitted:
                            if email and password:
                                auth_result = authenticate_user(email, password)
                                if auth_result:
                                    st.session_state.authenticated = True
                                    st.session_state.supabase_session = auth_result.get("session")
                                    st.session_state.user_email = email
                                    st.success("Login successful! Initializing platform...")
                                    st.rerun()
                                else:
                                    st.error("Invalid email or password. Please try again.")
                            else:
                                st.error("Please enter both email and password.")
                
                with tab2:
                    with st.form("signup_form", clear_on_submit=False):
                        email = st.text_input(
                            "Email", 
                            value="", 
                            key="signup_email",
                            placeholder="Enter your email"
                        )
                        password = st.text_input(
                            "Password", 
                            type="password", 
                            value="", 
                            key="signup_pass",
                            placeholder="Create a password"
                        )
                        confirm_password = st.text_input(
                            "Confirm Password", 
                            type="password", 
                            value="", 
                            key="signup_confirm_pass",
                            placeholder="Confirm your password"
                        )
                        
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                        with col_btn2:
                            submitted = st.form_submit_button(
                                "Create Account", 
                                type="primary",
                                use_container_width=True
                            )
                        
                        if submitted:
                            if email and password and confirm_password:
                                if password != confirm_password:
                                    st.error("Passwords do not match.")
                                elif len(password) < 6:
                                    st.error("Password must be at least 6 characters.")
                                else:
                                    # Sign up with redirect URL for email verification
                                    redirect_url = "http://localhost:8501"
                                    signup_result = sign_up_user(email, password, redirect_to=redirect_url)
                                    if signup_result:
                                        # Check if user needs email verification
                                        user = signup_result.get("user")
                                        if user and hasattr(user, 'email_confirmed_at') and user.email_confirmed_at:
                                            st.success("Account created successfully! You can now sign in.")
                                            st.session_state.authenticated = True
                                            st.session_state.supabase_session = signup_result.get("session")
                                            st.session_state.user_email = email
                                            st.rerun()
                                        else:
                                            st.success("Account created successfully!")
                                            st.info("Please check your email to verify your account. You can sign in after verification.")
                                            st.warning("Tip: If email verification is disabled in Supabase, you can sign in immediately.")
                                    else:
                                        st.error("Failed to create account. Email may already be registered.")
                            else:
                                st.error("Please fill in all fields.")
            else:
                # Fallback to simple authentication
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input(
                        "Username", 
                        value="", 
                        key="login_user",
                        placeholder="Enter your username"
                    )
                    password = st.text_input(
                        "Password", 
                        type="password", 
                        value="", 
                        key="login_pass",
                        placeholder="Enter your password"
                    )
                    
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    with col_btn2:
                        submitted = st.form_submit_button(
                            "Access Platform", 
                            type="primary",
                            use_container_width=True
                        )
                    
                    if submitted:
                        if username == "admin" and password == "admin123":
                            st.session_state.authenticated = True
                            st.success("Login successful! Initializing platform...")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Please try again.")
        
        # Footer removed per request
        st.stop()


    st.markdown(
        """
        <div style='text-align: center; padding: 2rem 0; margin-bottom: 2rem; border-bottom: 2px solid #1a1a1a;'>
            <h1 style='color: #ffffff; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.75rem; letter-spacing: -0.5px; text-shadow: 0 0 20px rgba(0, 255, 65, 0.5);'>
                Vulnerability Scrapper
            </h1>
            <div style='color: #cccccc; font-size: 1.1rem; font-weight: 400;'>
                Monitor critical and high-severity vulnerabilities from major IT/OT hardware and software OEMs
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )


    if not initialize_services():
        st.stop()

    st.sidebar.markdown(
        """
        <div style='text-align: center; padding: 1rem 0; margin-bottom: 2rem; border-bottom: 1px solid #1a1a1a;'>
            <h2 style='color: #00ff41; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; text-shadow: 0 0 15px rgba(0, 255, 65, 0.5);'>
                Control Center
            </h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    user_display = st.session_state.user_email if hasattr(st.session_state, 'user_email') and st.session_state.user_email else "Admin"
    st.sidebar.markdown(
        f"""
        <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 8px; padding: 1rem; margin-bottom: 2rem; 
                    border: 1px solid #00ff41; box-shadow: 0 0 20px rgba(0, 255, 65, 0.2);'>
            <div style='color: #ffffff; font-weight: 600; text-align: center; font-size: 0.95rem;'>
                Welcome, {user_display.split('@')[0] if '@' in user_display else user_display}!
            </div>
            <div style='color: #cccccc; font-size: 0.85rem; text-align: center; margin-top: 0.5rem;'>
                System Status: <span style='color: #00ff41; font-weight: 700; text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);'>OPERATIONAL</span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    page = st.sidebar.selectbox(
        "Navigation Menu",
        ["Dashboard", "Vulnerabilities", "Email Subscriptions", "Manual Scan", "Analytics", "Export Data", "Settings"]
    )


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
            <h2 style='color: #ffffff; font-size: 2rem; font-weight: 700; margin-bottom: 0.75rem; text-shadow: 0 0 15px rgba(0, 255, 65, 0.4);'>
                Dashboard Overview
            </h2>
            <div style='color: #cccccc; font-size: 1rem; font-weight: 400;'>
                Real-time vulnerability monitoring and threat intelligence
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    

    stats = st.session_state.db_ops.get_vulnerability_stats()
    scan_stats = st.session_state.db_ops.get_scan_stats()
    notification_stats = st.session_state.db_ops.get_notification_stats()
    

    st.markdown(
        """
        <div style='margin-bottom: 2rem;'>
            <h3 style='color: #00ff41; font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; text-shadow: 0 0 10px rgba(0, 255, 65, 0.4);'>
                Key Metrics
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 2rem; text-align: center; 
                        box-shadow: 0 0 25px rgba(255, 0, 0, 0.3), 0 4px 8px rgba(0, 0, 0, 0.5); border: 1px solid #ff3333;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #ff3333; 
                           font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-shadow: 0 0 15px rgba(255, 0, 0, 0.6);'>
                    {stats['total_vulnerabilities']}
                </div>
                <div style='color: #cccccc; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Total Vulnerabilities</div>
                <div style='color: #ff3333; font-size: 0.85rem; font-weight: 500; text-shadow: 0 0 8px rgba(255, 0, 0, 0.4);'>+{stats['recent_vulnerabilities']} (30 days)</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 2rem; text-align: center; 
                        box-shadow: 0 0 25px rgba(0, 255, 65, 0.3), 0 4px 8px rgba(0, 0, 0, 0.5); border: 1px solid #00ff41;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #00ff41; 
                           font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-shadow: 0 0 15px rgba(0, 255, 65, 0.6);'>
                    {stats['recent_vulnerabilities']}
                </div>
                <div style='color: #cccccc; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Recent Vulnerabilities</div>
                <div style='color: #00ff41; font-size: 0.85rem; font-weight: 500; text-shadow: 0 0 8px rgba(0, 255, 65, 0.4);'>Last 30 days</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 2rem; text-align: center; 
                        box-shadow: 0 0 25px rgba(0, 255, 65, 0.3), 0 4px 8px rgba(0, 0, 0, 0.5); border: 1px solid #00ff41;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #00ff41; 
                           font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-shadow: 0 0 15px rgba(0, 255, 65, 0.6);'>
                    {scan_stats['success_rate']:.1f}%
                </div>
                <div style='color: #cccccc; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Scan Success Rate</div>
                <div style='color: #00ff41; font-size: 0.85rem; font-weight: 500; text-shadow: 0 0 8px rgba(0, 255, 65, 0.4);'>{scan_stats['successful_scans']}/{scan_stats['total_scans']}</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 2rem; text-align: center; 
                        box-shadow: 0 0 25px rgba(0, 255, 65, 0.3), 0 4px 8px rgba(0, 0, 0, 0.5); border: 1px solid #00ff41;'>
                <div style='font-size: 2.5rem; margin-bottom: 0.5rem; color: #00ff41; 
                           font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-shadow: 0 0 15px rgba(0, 255, 65, 0.6);'>
                    {notification_stats['total_notifications']}
                </div>
                <div style='color: #cccccc; font-weight: 500; font-size: 0.9rem; text-transform: uppercase; 
                           letter-spacing: 0.5px; margin-bottom: 0.5rem;'>Email Notifications</div>
                <div style='color: #00ff41; font-size: 0.85rem; font-weight: 500; text-shadow: 0 0 8px rgba(0, 255, 65, 0.4);'>{notification_stats['success_rate']:.1f}% success rate</div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    

    st.markdown(
        """
        <div style='margin: 3rem 0 2rem 0;'>
            <h3 style='color: #00ff41; font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; text-shadow: 0 0 10px rgba(0, 255, 65, 0.4);'>
                Recent Critical & High Severity Vulnerabilities
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
    
   
    high_vulns = st.session_state.db_ops.get_vulnerabilities(
        severity="High",
        days_back=7,
        limit=10
    )
    
    all_recent = recent_vulns + high_vulns
    all_recent.sort(key=lambda x: x.published_date, reverse=True)
    
    if all_recent:

        for i, vuln in enumerate(all_recent[:5]):  
            severity_color = {
                'Critical': '#ff3333',
                'High': '#ff6666', 
                'Medium': '#ffcc00',
                'Low': '#00ff41'
            }.get(vuln.severity_level, '#cccccc')
            
            # Removed emoji icons
            
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; 
                            box-shadow: 0 0 20px {severity_color}30, 0 4px 8px rgba(0, 0, 0, 0.5); border-left: 4px solid {severity_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                            <div>
                            <div style='color: {severity_color}; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.25rem; text-shadow: 0 0 10px {severity_color}50;'>
                                    {vuln.severity_level} - {vuln.unique_id}
                                </div>
                            <div style='color: #cccccc; font-size: 0.9rem;'>{vuln.oem_name}</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: #00ff41; font-weight: 700; font-size: 1.1rem; text-shadow: 0 0 10px rgba(0, 255, 65, 0.5);'>
                                {vuln.cvss_score or 'N/A'}
                            </div>
                            <div style='color: #888888; font-size: 0.8rem;'>CVSS</div>
                        </div>
                    </div>
                    <div style='color: #ffffff; font-weight: 500; margin-bottom: 0.5rem; font-size: 1rem;'>
                        {vuln.product_name}
                    </div>
                    <div style='color: #cccccc; font-size: 0.9rem;'>
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
                    <h4 style='color: #00ff41; font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; text-shadow: 0 0 10px rgba(0, 255, 65, 0.4);'>
                        Additional Vulnerabilities
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
            <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 2rem; text-align: center; 
                        border: 1px solid #00ff41; box-shadow: 0 0 20px rgba(0, 255, 65, 0.2);'>
                <div style='color: #00ff41; font-weight: 700; font-size: 1.2rem; margin-bottom: 0.5rem; text-shadow: 0 0 15px rgba(0, 255, 65, 0.5);'>
                    No Recent Critical or High Severity Vulnerabilities
                </div>
                <div style='color: #cccccc; font-size: 0.95rem;'>
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
            <h3 style='color: #00ff41; font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; text-shadow: 0 0 10px rgba(0, 255, 65, 0.4);'>
                OEM Scanner Status
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
            status_color = '#00ff41' if is_enabled else '#ff3333'
            status_text = 'ACTIVE' if is_enabled else 'DISABLED'
            
            last_scan = scan_stats['last_scans_by_oem'].get(oem_id, 'Never')
            
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; 
                            box-shadow: 0 0 20px {status_color}30, 0 4px 8px rgba(0, 0, 0, 0.5); border-left: 4px solid {status_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                        <div style='color: {status_color}; font-weight: 700; font-size: 0.85rem; 
                                   text-transform: uppercase; letter-spacing: 0.5px; padding: 0.25rem 0.75rem;
                                   background: {status_color}20; border-radius: 6px; text-shadow: 0 0 10px {status_color}50;'>
                            {status_text}
                        </div>
                    </div>
                    <div style='color: #ffffff; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;'>
                        {status['name']}
                    </div>
                    <div style='color: #cccccc; font-size: 0.9rem; margin-bottom: 0.5rem;'>
                        {status['description']}
                    </div>
                    <div style='display: flex; justify-content: space-between; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #1a1a1a;'>
                        <div>
                            <div style='color: #888888; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Scan Interval</div>
                            <div style='color: #00ff41; font-size: 0.95rem; font-weight: 600; text-shadow: 0 0 8px rgba(0, 255, 65, 0.4);'>{status['scan_interval_hours']}h</div>
                        </div>
                        <div>
                            <div style='color: #888888; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Last Scan</div>
                            <div style='color: #ffffff; font-size: 0.95rem; font-weight: 500;'>{last_scan}</div>
                        </div>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )

def show_vulnerabilities():
    """Show vulnerabilities with enhanced filtering options"""
    st.header("Vulnerability Browser")
    
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
    """Show email and Slack subscription management"""
    st.header("Email & Slack Subscription Management")
    db_ops = st.session_state.db_ops
    all_subs = db_ops.get_subscriptions()
    if not all_subs:
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; border-left: 4px solid #00ff41; padding: 2rem; margin-bottom: 2rem; border: 1px solid #00ff41; box-shadow: 0 0 20px rgba(0, 255, 65, 0.2);'>
                <h3 style='color: #00ff41; font-weight: 700; margin-bottom: 1rem; text-shadow: 0 0 15px rgba(0, 255, 65, 0.5);'>No Subscriptions Yet!</h3>
                <p style='color: #cccccc; line-height: 1.6;'>For platform email alerts, add a quick test subscription below.<br>
                   <strong style='color: #ffffff;'>Demo suggestion:</strong> Email: <strong style='color: #00ff41;'>admin@example.com</strong>, OEM: <strong style='color: #00ff41;'>Intel</strong>, Severities: <strong style='color: #00ff41;'>Critical, High</strong></p>
            </div>
            """, unsafe_allow_html=True
        )
    
    # Add new subscription (auto-fill if none exist and form is blank)
    st.subheader("Add New Subscription")
    demo_email = "admin@example.com" if not all_subs else ""
    demo_oem = "Intel" if not all_subs else "All"
    demo_sev = ["Critical", "High"] if not all_subs else ["Critical"]

    with st.form("add_subscription"):
        notification_type = st.radio(
            "Notification Type",
            ["Email", "Slack", "Both"],
            horizontal=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email Address", value=demo_email if notification_type in ["Email", "Both"] else "", 
                                 disabled=(notification_type == "Slack"))
            slack_webhook = st.text_input(
                "Slack Webhook URL", 
                value="",
                help="Get webhook URL from Slack: Settings → Apps → Incoming Webhooks",
                disabled=(notification_type == "Email"),
                type="password"
            )
            oem_name = st.selectbox(
                "OEM (leave blank for all)",
                ["All"] + list(st.session_state.db_ops.get_vulnerability_stats()['oem_distribution'].keys()),
                index=(1 if demo_oem == "Intel" and "Intel" in st.session_state.db_ops.get_vulnerability_stats()['oem_distribution'] else 0)
            )
        with col2:
            product_name = st.text_input("Product Name (optional)")
            severity_filter = st.multiselect(
                "Severity Levels",
                ["Critical", "High", "Medium", "Low"],
                default=demo_sev
            )
        submitted = st.form_submit_button("Add Subscription")
        if submitted:
            if severity_filter:
                if notification_type == "Email" and not email:
                    st.error("Please provide an email address for email subscriptions.")
                elif notification_type == "Slack" and not slack_webhook:
                    st.error("Please provide a Slack webhook URL for Slack subscriptions.")
                elif notification_type == "Both" and (not email or not slack_webhook):
                    st.error("Please provide both email and Slack webhook URL.")
                else:
                    oem = None if oem_name == "All" else oem_name
                    severity_str = ",".join(severity_filter)
                    try:
                        # Add email subscription if needed
                        if notification_type in ["Email", "Both"]:
                            email_sub = st.session_state.db_ops.add_subscription(
                                email=email,
                                slack_webhook_url=None,
                                oem_name=oem,
                                product_name=product_name if product_name else None,
                                severity_filter=severity_str
                            )
                            st.success(f"Email subscription added successfully! ID: {email_sub.id}")
                        
                        # Add Slack subscription if needed
                        if notification_type in ["Slack", "Both"]:
                            slack_sub = st.session_state.db_ops.add_subscription(
                                email=None,
                                slack_webhook_url=slack_webhook,
                                oem_name=oem,
                                product_name=product_name if product_name else None,
                                severity_filter=severity_str
                            )
                            st.success(f"Slack subscription added successfully! ID: {slack_sub.id}")
                    except Exception as e:
                        st.error(f"Failed to add subscription: {e}")
            else:
                st.error("Please select at least one severity level.")
    
    # Manage existing subscriptions
    st.subheader("Manage Existing Subscriptions")
    
    subscriptions = st.session_state.db_ops.get_subscriptions()
    
    if subscriptions:
        df_subs = pd.DataFrame([{
            'ID': sub.id,
            'Email': sub.email or 'N/A',
            'Slack': 'Yes' if (hasattr(sub, 'slack_webhook_url') and sub.slack_webhook_url) else 'No',
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
    st.header("Manual Vulnerability Scan")
    
    st.subheader("Scan All OEMs")
    
    if st.button("Run Full Scan", type="primary"):
        with st.spinner("Scanning all OEMs for vulnerabilities..."):
            try:
                db_ops = st.session_state.db_ops
                known_ids = set(v.unique_id for v in db_ops.get_vulnerabilities(limit=1000000))
                results = st.session_state.scraper_manager.run_all_scrapers()
                
                total_found = 0
                total_new = 0
                total_emails_sent = 0
                any_subscription = bool(db_ops.get_subscriptions())
                new_ids = set()
                
                for oem_id, vulnerabilities in results.items():
                    st.markdown(f"<p style='color: #ffffff;'><strong>{oem_id.title()}:</strong> {len(vulnerabilities)} vulnerabilities found</p>", unsafe_allow_html=True)
                    
                    # Add vulnerabilities to database
                    for vuln_data in vulnerabilities:
                        try:
                            uid = vuln_data.get('unique_id')
                            if uid is None:
                                continue
                            
                            is_new = uid not in known_ids and uid not in new_ids
                            vuln = db_ops.add_vulnerability(vuln_data)
                            total_found += 1
                            
                            if is_new:
                                total_new += 1
                                new_ids.add(uid)
                                # Send email notifications
                                email_results = st.session_state.email_service.send_bulk_vulnerability_alerts(vuln)
                                if email_results['sent'] > 0:
                                    st.info(f"Sent {email_results['sent']} email notification{'s' if email_results['sent'] != 1 else ''} for {uid}.")
                                total_emails_sent += email_results['sent']
                                
                                # Send Slack notifications
                                slack_results = st.session_state.slack_service.send_bulk_vulnerability_alerts(vuln)
                                if slack_results['sent'] > 0:
                                    st.info(f"Sent {slack_results['sent']} Slack notification{'s' if slack_results['sent'] != 1 else ''} for {uid}.")
                                total_emails_sent += slack_results['sent']  # Reusing variable for total notifications
                        except Exception as e:
                            logger.error(f"Error adding vulnerability: {e}")
                total_existing = total_found - total_new
                st.success(f"Scan completed! Found {total_found} vulnerabilities, {total_new} new, {total_existing} already known.")
                if total_emails_sent > 0:
                    st.success(f"Total: Sent {total_emails_sent} email notification{'s' if total_emails_sent != 1 else ''} for new vulnerabilities.")
                elif any_subscription:
                    st.info("No email notifications sent (no matching new critical/high results for your current subscriptions). To test, add a subscription in the Email Subscriptions tab.")
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
                        db_ops = st.session_state.db_ops
                        known_ids = set(v.unique_id for v in db_ops.get_vulnerabilities(limit=1000000))
                        vulnerabilities = st.session_state.scraper_manager.run_scraper(oem_id)
                        new_count = 0
                        new_ids = set()
                        emails_sent = 0
                        any_subscription = bool(db_ops.get_subscriptions())
                        for vuln_data in vulnerabilities:
                            try:
                                uid = vuln_data.get('unique_id')
                                if uid is None:
                                    continue
                                is_new = uid not in known_ids and uid not in new_ids
                                vuln = db_ops.add_vulnerability(vuln_data)
                                if is_new:
                                    new_count += 1
                                    new_ids.add(uid)
                                    # Send email notifications
                                    email_notif = st.session_state.email_service.send_bulk_vulnerability_alerts(vuln)
                                    emails_sent += email_notif['sent']
                                    if email_notif['sent'] > 0:
                                        st.info(f"Sent {email_notif['sent']} email notification{'s' if email_notif['sent'] != 1 else ''} for {uid}.")
                                    
                                    # Send Slack notifications
                                    slack_notif = st.session_state.slack_service.send_bulk_vulnerability_alerts(vuln)
                                    emails_sent += slack_notif['sent']  # Reusing variable for total notifications
                                    if slack_notif['sent'] > 0:
                                        st.info(f"Sent {slack_notif['sent']} Slack notification{'s' if slack_notif['sent'] != 1 else ''} for {uid}.")
                            except Exception as e:
                                logger.error(f"Error adding vulnerability: {e}")
                        st.success(f"Found {len(vulnerabilities)} vulnerabilities, {new_count} new, {len(vulnerabilities)-new_count} already known.")
                        if emails_sent > 0:
                            st.success(f"Total: Sent {emails_sent} email notification{'s' if emails_sent != 1 else ''} for new vulnerabilities.")
                        elif any_subscription:
                            st.info("No email notifications sent (no matching new results for your current subscriptions).")
                    except Exception as e:
                        st.error(f"Scan failed: {e}")

def show_analytics():
    """Show analytics and charts"""
    st.header("Analytics & Insights")
    
    # Get statistics
    stats = st.session_state.db_ops.get_vulnerability_stats()
    
    # Severity distribution
    st.subheader("Vulnerability Severity Distribution")
    
    if stats['severity_distribution']:
        fig_severity = px.pie(
            values=list(stats['severity_distribution'].values()),
            names=list(stats['severity_distribution'].keys()),
            title="Vulnerabilities by Severity",
            color_discrete_sequence=['#ff3333', '#ff6666', '#ffcc00', '#00ff41', '#cccccc']
        )
        fig_severity.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            title_font_color='#00ff41',
            legend_font_color='#cccccc'
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
            labels={'x': 'OEM', 'y': 'Count'},
            color_discrete_sequence=['#00ff41']
        )
        fig_oem.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            title_font_color='#00ff41',
            legend_font_color='#cccccc'
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
            labels={'x': 'Date', 'y': 'Count'},
            color_discrete_sequence=['#00ff41']
        )
        fig_trend.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#ffffff',
            title_font_color='#00ff41',
            legend_font_color='#cccccc'
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
    st.header("Export Data")
    
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
                label="Download CSV",
                data=csv_data,
                file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col2:
            # JSON Export
            json_data = df_export.to_json(orient='records', indent=2)
            st.download_button(
                label="Download JSON",
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
                    label="Download Excel",
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
    st.header("Settings & Configuration")
    
    # Email configuration
    st.subheader("Email Configuration")
    
    # Check if email service is initialized
    if st.session_state.email_service is None:
        st.warning("⚠️ Email service not initialized. Please refresh the page.")
        if st.button("Initialize Email Service"):
            try:
                st.session_state.email_service = create_email_service(st.session_state.db_ops)
                st.success("✅ Email service initialized!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to initialize email service: {str(e)}")
    else:
        # Show current email configuration (masked)
        email_username = st.session_state.email_service.email_username if st.session_state.email_service.email_username else "Not configured"
        smtp_server = st.session_state.email_service.smtp_server if st.session_state.email_service.smtp_server else "Not configured"
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Email:** {email_username}")
        with col2:
            st.write(f"**SMTP Server:** {smtp_server}")
        
        if st.button("Test Email Configuration"):
            with st.spinner("Testing email configuration..."):
                try:
                    # Ensure email service is properly initialized
                    if st.session_state.email_service is None:
                        st.session_state.email_service = create_email_service(st.session_state.db_ops)
                    
                    # Test the configuration
                    import logging
                    logging.basicConfig(level=logging.INFO)
                    
                    success = st.session_state.email_service.test_email_configuration()
                    
                    if success:
                        st.success("✅ Email configuration test successful! Check your inbox at " + st.session_state.email_service.email_username)
                    else:
                        st.error("❌ Email configuration test failed.")
                        
                        # Show configuration details
                        st.warning("**Current Configuration:**")
                        st.write(f"- Email: {st.session_state.email_service.email_username}")
                        st.write(f"- SMTP Server: {st.session_state.email_service.smtp_server}:{st.session_state.email_service.smtp_port}")
                        st.write(f"- Password: {'✅ Set' if st.session_state.email_service.email_password else '❌ Not set'}")
                        
                        st.info("💡 **Troubleshooting Steps:**\n"
                               "1. Verify your Gmail App Password is correct\n"
                               "2. Make sure 2-Factor Authentication is enabled\n"
                               "3. Check that there are no extra spaces in the app password\n"
                               "4. Verify SMTP settings in your .env file\n"
                               "5. Check the terminal/console where Streamlit is running for detailed error messages")
                        
                        # Try to get more details
                        try:
                            import yagmail
                            test_yag = yagmail.SMTP(
                                st.session_state.email_service.email_username,
                                st.session_state.email_service.email_password
                            )
                            test_yag.close()
                            st.info("✅ Direct SMTP connection test passed - issue might be with email sending")
                        except Exception as smtp_error:
                            st.error(f"❌ SMTP Connection Error: {str(smtp_error)}")
                            
                except Exception as e:
                    st.error(f"❌ Error testing email configuration: {str(e)}")
                    st.info("💡 Check the terminal/console for detailed error messages")
                    import traceback
                    with st.expander("Show detailed error traceback"):
                        st.code(traceback.format_exc())
                    
                    # Try to diagnose the issue
                    st.warning("**Diagnostics:**")
                    try:
                        if st.session_state.email_service:
                            st.write(f"- Email service exists: ✅")
                            st.write(f"- Email username: {st.session_state.email_service.email_username}")
                            st.write(f"- SMTP server: {st.session_state.email_service.smtp_server}")
                        else:
                            st.write("- Email service: ❌ Not initialized")
                    except:
                        st.write("- Could not access email service")
    
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
