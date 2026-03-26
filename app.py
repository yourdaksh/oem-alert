import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()

from database import get_db, init_database
from database.operations import DatabaseOperations
from database.models import Vulnerability, Subscription, ScanLog
from scrapers import create_scraper_manager
from email_notifications import create_email_service
from slack_notifications import create_slack_service
from config import get_all_oems, get_enabled_oems
from utils.supabase_client import authenticate_user, is_supabase_enabled, sign_up_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Vulnerability Scraper",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)


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
        if st.session_state.db_ops is None:
            init_database()
            
            db = next(get_db())
            st.session_state.db_ops = DatabaseOperations(db)
        
        if st.session_state.scraper_manager is None:
            st.session_state.scraper_manager = create_scraper_manager()
        
        if st.session_state.email_service is None:
            st.session_state.email_service = create_email_service(st.session_state.db_ops)
        
        if st.session_state.slack_service is None:
            st.session_state.slack_service = create_slack_service(st.session_state.db_ops)
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return False

def get_allowed_oems():
    """Get list of allowed OEMs for the current user's organization"""
    user = st.session_state.get("user")
    if not user or not user.organization_id:
        return None
        
    org = st.session_state.db_ops.get_organization(user.organization_id)
    if not org or not org.enabled_oems or org.enabled_oems == "ALL":
        return None
        
    return [oem.strip() for oem in org.enabled_oems.split(",") if oem.strip()]

def main():
    """Main application function with authentication and improved UI"""

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

        /* --- Global Variables --- */
        :root {
            --primary-color:
            --primary-hover:
            --accent-red:
            --bg-dark:
            --bg-card: rgba(10, 10, 10, 0.9);
            --bg-card-border: rgba(57, 255, 20, 0.2);
            --text-main:
            --text-muted:
            --font-heading: 'Space Grotesk', sans-serif;
            --font-body: 'Inter', sans-serif;
        }

        /* --- Global Reset & Typography --- */
        html, body, [class*="css"] {
            font-family: var(--font-body) !important;
            background: var(--bg-dark) !important;
            color: var(--text-main) !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-heading) !important;
            letter-spacing: -0.5px;
        }

        /* --- Main Background --- */
        .main, .stApp, .block-container {
            background: var(--bg-dark) !important;
        }

        /* --- Scrollbars --- */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background:
            border-radius: 4px; border: 1px solid var(--accent-red);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-red);
        }

        /* --- Components: Buttons --- */
        .stButton>button {
            background: transparent !important;
            color: var(--primary-color) !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1px solid var(--primary-color) !important;
            padding: 0.6rem 1.2rem !important;
            box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
            transition: all 0.3s ease !important;
        }
        
        .stButton>button:hover {
            background: rgba(57, 255, 20, 0.1) !important;
            box-shadow: 0 0 20px rgba(57, 255, 20, 0.6);
            border-color: var(--primary-color) !important;
        }
        
        .stButton>button:active {
            transform: translateY(0);
        }

        /* --- Components: Inputs --- */
        .stTextInput>div>div>input, .stSelectbox>div>div>div {
            background: rgba(15, 15, 15, 0.8) !important;
            color: var(--text-main) !important;
            border: 1px solid rgba(255, 7, 58, 0.3) !important;
            border-radius: 8px !important;
            transition: all 0.2s ease;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: var(--accent-red) !important;
            box-shadow: 0 0 10px rgba(255, 7, 58, 0.5) !important;
        }

        /* --- Components: Cards --- */
        div[data-testid="stMetricValue"] {
            font-family: var(--font-heading) !important;
            color: var(--primary-color) !important;
            text-shadow: 0 0 10px rgba(57, 255, 20, 0.5);
        }
        
        /* --- Sidebar Polish --- */
        section[data-testid="stSidebar"] {
            background: rgba(0, 0, 0, 1.0) !important;
            border-right: 1px solid rgba(255, 7, 58, 0.3);
        }
        
        /* --- Custom Utility Classes --- */
        .glass-card {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--bg-card-border);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 0 15px rgba(57, 255, 20, 0.1);
        }
        
        .neon-text {
            color: var(--primary-color);
            text-shadow: 0 0 10px rgba(57, 255, 20, 0.6);
        }
        
        .neon-text-red {
            color: var(--accent-red);
            text-shadow: 0 0 10px rgba(255, 7, 58, 0.6);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None

    if not initialize_services():
        st.error("Failed to initialize application services.")
        st.stop()


    query_params = st.query_params
    invite_token = query_params.get("token")

    if not st.session_state.authenticated:
        
        st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        
        with col2:
            st.markdown(
                """
                <div style='text-align: center; margin-bottom: 2rem;'>
                    <div style='font-size: 4rem; margin-bottom: 0.5rem; animation: float 6s ease-in-out infinite;'></div>
                    <h1 style='font-family: "Space Grotesk"; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;'>
                        <span style='color: #fff;'>VULNERABILITY</span> <span class='neon-text'>SCRAPER</span>
                    </h1>
                    <p style='color: var(--text-muted); font-size: 1rem;'>
                        Next-Gen Vulnerability Intelligence Platform
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            use_supabase_auth = is_supabase_enabled()
            
            if use_supabase_auth:
                tab1, tab2 = st.tabs([" Sign In", " Sign Up"])
                
                with tab1:
                    with st.form("login_form", clear_on_submit=False):
                        email = st.text_input("Email", placeholder="admin@example.com")
                        password = st.text_input("Password", type="password", placeholder="••••••••")
                        
                        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                        
                        if st.form_submit_button("Access Platform", use_container_width=True):
                            auth_result = authenticate_user(email, password)
                            if auth_result:
                                st.session_state.authenticated = True
                                st.session_state.supabase_session = auth_result.get("session")
                                st.session_state.user_email = email
                                st.success("Login successful! Initializing platform...")
                                st.rerun()
                            else:
                                st.error("Invalid email or password")
                
                with tab2:
                    with st.form("register_org_form"):
                        st.write("Create a new Organization")
                        org_name = st.text_input("Organization Name", placeholder="Acme Corp")
                        admin_username = st.text_input("Admin Username", placeholder="admin_user")
                        admin_email = st.text_input("Admin Email", placeholder="admin@acme.com")
                        admin_password = st.text_input("Admin Password", type="password")
                        
                        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

                        if st.form_submit_button(" Launch Organization", use_container_width=True):
                            org = st.session_state.db_ops.create_organization(org_name)
                            if org:
                                signup_result = sign_up_user(admin_email, admin_password)
                                if signup_result:
                                    user = st.session_state.db_ops.create_user(
                                        username=admin_username,
                                        email=admin_email,
                                        password=admin_password,
                                        role="Owner",
                                        org_id=org.id
                                    )
                                    st.success("Registration successful! Please login.")
                                else:
                                    st.error("Failed to create Supabase account.")
                            else:
                                st.error("Failed to create organization.")
            else:
                if invite_token:
                    st.info(" You have been invited to join an organization!")
                    invite = st.session_state.db_ops.get_invitation_by_token(invite_token)
                    
                    if invite:
                        st.write(f"Joining as **{invite.role}**")
                        with st.form("accept_invite_form"):
                            new_username = st.text_input("Choose Username", placeholder="e.g., cyber_ninja")
                            new_password = st.text_input("Choose Password", type="password")
                            confirm_password = st.text_input("Confirm Password", type="password")
                            
                            submit_btn = st.form_submit_button("Complete Registration", use_container_width=True)
                            if submit_btn:
                                if new_password != confirm_password:
                                    st.error("Passwords do not match")
                                elif not new_username:
                                    st.error("Username required")
                                else:
                                    user = st.session_state.db_ops.accept_invitation(invite_token, new_username, new_password)
                                    if user:
                                        st.success("Registration successful! Please login.")
                                        st.query_params.clear()
                                    else:
                                        st.error("Registration failed.")
                    else:
                        st.error("Invalid or expired invitation token.")

                else:
                    with st.form("login_form"):
                        email = st.text_input("Email", placeholder="admin@example.com")
                        password = st.text_input("Password", type="password", placeholder="••••••••")
                        
                        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
                        
                        if st.form_submit_button("Access Platform", use_container_width=True):
                            user = st.session_state.db_ops.verify_login(email, password)
                            if user:
                                st.session_state.authenticated = True
                                st.session_state.user = user
                                st.success(f"Welcome back, {user.username}!")
                                st.rerun()
                            else:
                                st.error("Invalid email or password")
                    
                    st.markdown(
                        "<div style='text-align: center; margin-top: 1rem;'>"
                        "<a href='#' style='color: #39FF14; text-decoration: none; font-size: 0.85rem;'>Forgot password?</a>"
                        "</div>",
                        unsafe_allow_html=True
                    )
            
            st.markdown(
                """
                <div style='text-align: center; margin-top: 2rem; color: #555; font-size: 0.8rem;'>
                    &copy; 2026 Vulnerability Scraper Intelligence | Secure Access Only
                </div>
                """,
                unsafe_allow_html=True
            )

        
        st.stop()


    st.sidebar.markdown(
        """
        <div style='text-align: center; padding: 1rem 0; margin-bottom: 2rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem; text-shadow: 0 0 15px rgba(57, 255, 20, 0.5);'></div>
            <h2 style='color: #39FF14; font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; 
                       text-shadow: 0 0 10px rgba(57, 255, 20, 0.3); font-family: "Space Grotesk", sans-serif;'>
                CONTROL CENTER
            </h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    user = st.session_state.get("user")
    
    if st.session_state.get("authenticated") and not user:
         user_display = st.session_state.get("user_email", "Admin")
    else:
         user_display = user.username if user else "Admin"

    st.sidebar.markdown(
        f"""
        <div style='background: rgba(57, 255, 20, 0.1); border-radius: 12px; padding: 1rem; margin-bottom: 2rem; 
                    border: 1px solid rgba(57, 255, 20, 0.3);'>
            <div style='color: #39FF14; font-weight: 600; text-align: center;'>
                 Welcome, {user_display}!
            </div>
            <div style='color: #a0a0a0; font-size: 0.9rem; text-align: center; margin-top: 0.5rem;'>
                System Status: <span style='color: #39FF14;'> OPERATIONAL</span>
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )


    nav_options = ["Dashboard", "Kanban Board", "Vulnerabilities", "Email Subscriptions", "Manual Scan", "Analytics", "Export Data", "Settings"]
    
    if user and user.role == "Analyst":
        if "Manual Scan" in nav_options:
            nav_options.remove("Manual Scan")
    
    user = st.session_state.get("user")
    if user and user.organization_id:
        nav_options.insert(3, "My Tasks")
        if user.role in ["Owner", "Team Lead"]:
            nav_options.insert(4, "Team Management")
        
    page = st.sidebar.selectbox(
        " Navigation Menu",
        nav_options,
        format_func=lambda x: {
            "Dashboard": "📊 Dashboard",
            "Kanban Board": "📋 Kanban Board",
            "Vulnerabilities": "🛡️ Vulnerabilities", 
            "My Tasks": "✅ My Tasks",
            "Team Management": "👥 Team Management",
            "Email Subscriptions": "📧 Email Subscriptions",
            "Manual Scan": "🔍 Manual Scan",
            "Analytics": "📈 Analytics",
            "Export Data": "📥 Export Data",
            "Settings": "⚙️ Settings"
        }.get(x, x)

    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Kanban Board":
        show_kanban_board()
    elif page == "Vulnerabilities":
        show_vulnerabilities()
    elif page == "My Tasks":
        show_my_tasks()
    elif page == "Team Management":
        show_team_management()
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

    st.sidebar.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

def show_my_tasks():
    """Show vulnerabilities assigned to the current user"""
    st.header(" My Assigned Tasks")
    
    user = st.session_state.get("user")
    if not user:
        st.error("Please login to view tasks.")
        return

    tasks = st.session_state.db_ops.get_user_assigned_vulnerabilities(user.id)
    
    if not tasks:
        st.info(" No tasks assigned to you!")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assigned", len(tasks))
    with col2:
        open_tasks = len([t for t in tasks if t.status not in ['Resolved', 'Closed', 'Mitigated']])
        st.metric("Open / In Progress", open_tasks)
    with col3:
        completed = len([t for t in tasks if t.status in ['Resolved', 'Closed', 'Mitigated']])
        st.metric("Completed", completed)

    st.divider()

    for vuln in tasks:
        status_color_map = {
            "Open": "#FF073A",
            "Investigating": "#FF9500",
            "Mitigated": "#39FF14",
            "False Positive": "#888888",
            "Assigned": "#00A8CC",
            "Resolved": "#39FF14",
            "Closed": "#555555"
        }
        status_color = status_color_map.get(vuln.status, "#00A8CC")
        
        st.markdown(
            f"""
            <div class="glass-card" style="border-left: 4px solid {status_color}; margin-bottom: 1rem; padding: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <div>
                        <span style="background-color: {status_color}20; color: {status_color}; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; border: 1px solid {status_color}40;">
                            {vuln.status.upper()}
                        </span>
                        <span style="background-color: #333; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-left: 10px; border: 1px solid #444;">
                            {vuln.severity_level.upper()}
                        </span>
                    </div>
                     <div style="color: #666; font-size: 0.9rem; font-family: 'JetBrains Mono', monospace;">
                        {vuln.assigned_at.strftime('%Y-%m-%d') if vuln.assigned_at else 'N/A'}
                    </div>
                </div>
                <h3 style="margin: 0 0 5px 0; font-family: 'Space Grotesk'; font-size: 1.3rem; color: #fff;">
                    {vuln.product_name} 
                </h3>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #39FF14; margin-bottom: 10px;">
                    {vuln.unique_id}
                </div>
                <div style="color: #aaa; font-size: 0.9rem; margin-bottom: 10px;">
                    <strong>Assigned By:</strong> {vuln.assigned_by.username if vuln.assigned_by else 'Unknown'} &nbsp;•&nbsp; 
                    <strong>OEM:</strong> {vuln.oem_name}
                </div>
                <div style="color: #ddd; font-size: 0.95rem; line-height: 1.5; margin-bottom: 0;">
                    {vuln.vulnerability_description[:200] + '...' if len(vuln.vulnerability_description) > 200 else vuln.vulnerability_description}
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        with st.expander(" Update Status & Notes"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Full Description:**<br>{vuln.vulnerability_description}", unsafe_allow_html=True)
                st.divider()
                
                new_status = st.selectbox("Update Status", ["Investigating", "Mitigated", "Resolved", "False Positive"], key=f"mytask_status_{vuln.id}")
                if st.button("Update", key=f"mytask_update_{vuln.id}"):
                    st.session_state.db_ops.update_vulnerability_status(vuln.id, new_status, user.username)
                    st.success("Status Updated")
                    st.rerun()
            
            with c2:
                resolution_note = st.text_area("Resolution Notes", value=vuln.resolution_notes or "", key=f"mytask_note_{vuln.id}")
                if st.button("Save Notes", key=f"mytask_save_{vuln.id}"):
                    if st.session_state.db_ops.set_resolution_notes(vuln.id, resolution_note):
                        st.success("Notes saved")
                        st.rerun()
                    else:
                        st.error("Failed to save notes")


from utils.report_generator import generate_pdf_report


def show_kanban_board():
    """Kanban board for visual vulnerability tracking"""
    st.header("📋 Kanban Board")
    
    user = st.session_state.get("user")
    allowed_oems = get_allowed_oems()
    db_ops = st.session_state.db_ops
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        all_oems = get_all_oems()
        filter_oem = st.selectbox("Filter by OEM", ["All"] + list(all_oems.keys()), key="kanban_oem")
    with col_f2:
        filter_severity = st.selectbox("Filter by Severity", ["All", "Critical", "High", "Medium", "Low"], key="kanban_sev")
    with col_f3:
        if user and user.organization_id:
            team = db_ops.get_organization_users(user.organization_id)
            assignee_names = {u.id: u.username for u in team}
            filter_assignee = st.selectbox("Filter by Assignee", ["All"] + [u.username for u in team], key="kanban_assignee")
        else:
            filter_assignee = "All"
            assignee_names = {}
    
    st.divider()
    
    kanban_statuses = ["Open",  "Assigned", "In Progress", "Resolved", "Closed"]
    status_colors = {
        "Open": "#FF073A",
        "Assigned": "#00A8CC", 
        "In Progress": "#FF9500",
        "Resolved": "#39FF14",
        "Closed": "#555555"
    }
    status_icons = {
        "Open": "🔴", "Assigned": "🔵", "In Progress": "🟡", "Resolved": "🟢", "Closed": "⚫"
    }
    
    cols = st.columns(len(kanban_statuses))
    
    for i, status in enumerate(kanban_statuses):
        with cols[i]:
            color = status_colors.get(status, "#888")
            st.markdown(
                f"""
                <div style='background: {color}15; border: 1px solid {color}40; border-radius: 12px; padding: 0.8rem; text-align: center; margin-bottom: 1rem;'>
                    <span style='font-size: 1.1rem; font-weight: 700; color: {color};'>{status_icons.get(status, '')} {status.upper()}</span>
                </div>
                """, unsafe_allow_html=True
            )
            
            vulns = db_ops.get_vulnerabilities_by_status(status, allowed_oems)
            
            if filter_oem != "All":
                vulns = [v for v in vulns if v.oem_name == filter_oem]
            if filter_severity != "All":
                vulns = [v for v in vulns if v.severity_level == filter_severity]
            if filter_assignee != "All":
                vulns = [v for v in vulns if v.assigned_to and v.assigned_to.username == filter_assignee]
            
            st.caption(f"{len(vulns)} items")
            
            for vuln in vulns[:15]:
                sev_colors = {"Critical": "#FF073A", "High": "#FF6B35", "Medium": "#FF9500", "Low": "#39FF14"}
                sev_color = sev_colors.get(vuln.severity_level, "#888")
                assignee_name = vuln.assigned_to.username if vuln.assigned_to else "Unassigned"
                
                st.markdown(
                    f"""
                    <div style='background: rgba(20,20,20,0.9); border: 1px solid {color}30; border-left: 3px solid {sev_color};
                                border-radius: 8px; padding: 0.7rem; margin-bottom: 0.5rem; font-size: 0.82rem;'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
                            <span style='color: {sev_color}; font-weight: 700; font-size: 0.7rem;'>{vuln.severity_level.upper()}</span>
                            <span style='color: #666; font-size: 0.7rem;'>{vuln.oem_name}</span>
                        </div>
                        <div style='color: #fff; font-weight: 600; margin-bottom: 4px; line-height: 1.3;'>{vuln.product_name[:40]}</div>
                        <div style='color: #39FF14; font-family: monospace; font-size: 0.7rem; margin-bottom: 4px;'>{vuln.unique_id}</div>
                        <div style='color: #888; font-size: 0.7rem;'>👤 {assignee_name}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                with st.popover(f"✏️ Move", use_container_width=True):
                    move_options = [s for s in kanban_statuses if s != status]
                    new_s = st.selectbox("Move to", move_options, key=f"kbn_move_{vuln.id}")
                    
                    if user and user.organization_id:
                        team = db_ops.get_organization_users(user.organization_id)
                        assign_to = st.selectbox("Assign to", ["--"] + [u.username for u in team], key=f"kbn_assign_{vuln.id}")
                    else:
                        assign_to = "--"
                    
                    if st.button("Apply", key=f"kbn_apply_{vuln.id}"):
                        db_ops.update_vulnerability_status(vuln.id, new_s, user.username if user else "Admin")
                        if assign_to != "--" and user:
                            target_user = next((u for u in team if u.username == assign_to), None)
                            if target_user:
                                db_ops.assign_vulnerability(vuln.id, target_user.id, user.id)
                        st.rerun()


def show_team_management():
    """Full team management CRM page with role-based access"""
    user = st.session_state.get("user")
    if not user:
        st.error("Please login to access team management.")
        return
    
    is_owner = user.role == "Owner"
    is_lead = user.role == "Team Lead"
    
    st.header("👥 Team Management")
    
    if not user.organization_id:
        st.warning("You are not part of an organization.")
        return
    
    db_ops = st.session_state.db_ops
    org = db_ops.get_organization(user.organization_id)
    team_members = db_ops.get_organization_users(user.organization_id)
    
    st.markdown(
        f"""
        <div class="glass-card" style="padding: 1.5rem; margin-bottom: 2rem;">
            <h3 style='color: #39FF14; margin: 0 0 0.5rem 0;'>🏢 {org.name if org else 'Unknown'}</h3>
            <div style='display: flex; gap: 2rem; color: #aaa;'>
                <span>👥 <strong style='color:#fff;'>{len(team_members)}</strong> Members</span>
                <span>🛡️ <strong style='color:#fff;'>{org.enabled_oems if org and org.enabled_oems else 'ALL'}</strong> OEMs Tracked</span>
                <span>📋 Your Role: <strong style='color: #39FF14;'>{user.role}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    
    st.subheader("Team Members")
    
    role_colors = {"Owner": "#FFD700", "Team Lead": "#00A8CC", "Analyst": "#39FF14"}
    
    for member in team_members:
        stats = db_ops.get_user_activity_stats(member.id)
        role_color = role_colors.get(member.role, "#888")
        is_self = member.id == user.id
        
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
            
            with c1:
                self_tag = " (You)" if is_self else ""
                st.markdown(
                    f"""
                    <div style='padding: 0.5rem 0;'>
                        <div style='color: #fff; font-weight: 600;'>{member.username}{self_tag}</div>
                        <div style='color: #888; font-size: 0.8rem;'>{member.email}</div>
                    </div>
                    """, unsafe_allow_html=True
                )
            
            with c2:
                st.markdown(
                    f"<span style='background: {role_color}20; color: {role_color}; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; border: 1px solid {role_color}40;'>{member.role}</span>",
                    unsafe_allow_html=True
                )
            
            with c3:
                st.markdown(f"<div style='color:#aaa; font-size:0.85rem; padding-top:0.5rem'>📊 {stats['total_assigned']} assigned</div>", unsafe_allow_html=True)
            
            with c4:
                st.markdown(f"<div style='color:#39FF14; font-size:0.85rem; padding-top:0.5rem'>✅ {stats['resolved']} resolved</div>", unsafe_allow_html=True)
            
            with c5:
                if is_owner and not is_self:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        new_role = st.selectbox("Role", ["Analyst", "Team Lead", "Owner"], key=f"role_{member.id}", 
                                              index=["Analyst", "Team Lead", "Owner"].index(member.role))
                        if new_role != member.role:
                            if st.button("Save", key=f"save_role_{member.id}"):
                                db_ops.update_user_role(member.id, new_role)
                                st.success(f"Role updated to {new_role}")
                                st.rerun()
                    with col_b:
                        if st.button("🗑️", key=f"remove_{member.id}", help="Remove member"):
                            db_ops.remove_user(member.id)
                            st.success(f"Removed {member.username}")
                            st.rerun()
            
            st.divider()
    
    if is_owner:
        st.subheader("➕ Invite New Member")
        
        with st.form("invite_form"):
            inv_c1, inv_c2, inv_c3 = st.columns([3, 2, 1])
            with inv_c1:
                invite_email = st.text_input("Email Address", placeholder="analyst@company.com")
            with inv_c2:
                invite_role = st.selectbox("Role", ["Analyst", "Team Lead"])
            with inv_c3:
                invite_password = st.text_input("Temp Password", type="password", placeholder="••••••••")
            
            if st.form_submit_button("Invite Member", use_container_width=True):
                if invite_email and invite_password:
                    existing = db_ops.get_user_by_email(invite_email)
                    if existing:
                        st.error(f"{invite_email} is already a member.")
                    else:
                        new_user = db_ops.create_user(
                            username=invite_email,
                            email=invite_email,
                            password=invite_password,
                            role=invite_role,
                            org_id=user.organization_id
                        )
                        if new_user:
                            st.success(f"✅ {invite_email} added as {invite_role}!")
                            st.rerun()
                        else:
                            st.error("Failed to create user.")
                else:
                    st.warning("Please fill in email and temporary password.")
    
    elif is_lead:
        st.info("💡 As a Team Lead, you can view the team and assign tasks. Contact the Owner to manage roles.")


def show_dashboard():
    """Show main dashboard with creative overview"""
    
    with st.sidebar:
        st.divider()
        st.markdown("###  Reports")
        if st.button("Download Weekly Briefing"):
            with st.spinner("Generating PDF..."):
                recent_vulns = st.session_state.db_ops.get_vulnerabilities(days_back=30, limit=50)
                pdf_bytes = generate_pdf_report(recent_vulns)
                
                st.download_button(
                    label=" Click to Download PDF",
                    data=pdf_bytes,
                    file_name=f"Executive_Briefing_{datetime.now().strftime('%Y-%m-%d')}.pdf",
                    mime="application/pdf"
                )
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 3rem;'>
            <h2 style='color: #39FF14; font-size: 2rem; font-weight: 600; margin-bottom: 1rem; 
                       text-shadow: 0 0 15px rgba(57, 255, 20, 0.3); font-family: "Space Grotesk", sans-serif;'>
                 DASHBOARD OVERVIEW
            </h2>
            <div style='color: #cccccc; font-size: 1rem; font-weight: 400;'>
                Real-time vulnerability monitoring and threat intelligence
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    

    allowed_oems = get_allowed_oems()
    stats = st.session_state.db_ops.get_vulnerability_stats(allowed_oems=allowed_oems)
    scan_stats = st.session_state.db_ops.get_scan_stats()
    notification_stats = st.session_state.db_ops.get_notification_stats()
    

    st.markdown("###  Key Performance Indicators")

    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #ff6347; margin-bottom: 0.5rem; font-family: 'Space Grotesk';">
                    {stats['total_vulnerabilities']}
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">
                    Total Vulnerabilities
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #ffc107; margin-bottom: 0.5rem; font-family: 'Space Grotesk';">
                    {stats['recent_vulnerabilities']}
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">
                    New (30 Days)
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; font-weight: 700; color: var(--primary-color); margin-bottom: 0.5rem; font-family: 'Space Grotesk';">
                    {scan_stats['success_rate']:.1f}%
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">
                    Scan Success
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 2.5rem; font-weight: 700; color: #a0a0a0; margin-bottom: 0.5rem; font-family: 'Space Grotesk';">
                    {notification_stats['total_sent']}
                </div>
                <div style="color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">
                    Alerts Sent
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    

    st.markdown(
        """
        <div style='margin: 3rem 0 2rem 0;'>
            <h3 style='color: #39FF14; font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; 
                       text-shadow: 0 0 10px rgba(57, 255, 20, 0.3); font-family: "Space Grotesk", sans-serif;'>
                 RECENT CRITICAL & HIGH SEVERITY VULNERABILITIES
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    recent_vulns = st.session_state.db_ops.get_vulnerabilities(
        severity="Critical",
        days_back=7,
        limit=10,
        allowed_oems=allowed_oems
    )
    
   
    high_vulns = st.session_state.db_ops.get_vulnerabilities(
        severity="High",
        days_back=7,
        limit=10,
        allowed_oems=allowed_oems
    )
    
    all_recent = recent_vulns + high_vulns
    all_recent.sort(key=lambda x: x.published_date, reverse=True)
    
    if all_recent:

        for i, vuln in enumerate(all_recent[:5]):  
            severity_color = {
                'Critical': '#FF073A',
                'High': '#FF3366', 
                'Medium': '#FF9500',
                'Low': '#39FF14'
            }.get(vuln.severity_level, '#8e8e93')
            
            severity_icon = {
                'Critical': '🚨',
                'High': '⚠️',
                'Medium': 'ℹ️',
                'Low': '✅'
            }.get(vuln.severity_level, '')
            
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; 
                            box-shadow: 0 0 20px {severity_color}30, 0 4px 8px rgba(0, 0, 0, 0.5); border-left: 4px solid {severity_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                            <div>
                            <div style='color: {severity_color}; font-weight: 700; font-size: 1.1rem; margin-bottom: 0.25rem; text-shadow: 0 0 10px {severity_color}50;'>
                                     {severity_icon} {vuln.severity_level} - {vuln.unique_id}
                                </div>
                            <div style='color: #cccccc; font-size: 0.9rem;'>{vuln.oem_name}</div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='color: #39FF14; font-weight: 600; font-family: "JetBrains Mono", monospace;'>
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
        
        if len(all_recent) > 5:
            st.markdown(
                """
                <div style='margin-top: 2rem;'>
                    <h4 style='color: #39FF14; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; 
                               text-shadow: 0 0 10px rgba(57, 255, 20, 0.3); font-family: "Space Grotesk", sans-serif;'>
                         ADDITIONAL VULNERABILITIES
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
                        border: 2px solid rgba(57, 255, 20, 0.3);'>
                <div style='font-size: 2rem; margin-bottom: 1rem; color: #39FF14;'>🛡️</div>
                <div style='color: #39FF14; font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem;'>
                    No Recent Critical or High Severity Vulnerabilities
                </div>
                <div style='color: #cccccc; font-size: 0.95rem;'>
                    All systems are secure! No new critical or high-severity vulnerabilities found in the last 7 days.
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    st.markdown(
        """
        <div style='margin: 3rem 0 2rem 0;'>
            <h3 style='color: #39FF14; font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; 
                       text-shadow: 0 0 10px rgba(57, 255, 20, 0.3); font-family: "Space Grotesk", sans-serif;'>
                 OEM SCANNER STATUS
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    scraper_status = st.session_state.scraper_manager.get_scraper_status()
    if allowed_oems:
        scraper_status = {k: v for k, v in scraper_status.items() if k in allowed_oems}
    
    cols = st.columns(3)
    for i, (oem_id, status) in enumerate(scraper_status.items()):
        with cols[i % 3]:
            is_enabled = status['enabled']
            status_color = '#39FF14' if is_enabled else '#ff3b30'
            status_icon = '🟢' if is_enabled else '🔴'
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
                            {status_icon} {status_text}
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
                            <div style='color: #39FF14; font-size: 0.8rem; font-weight: 600;'>SCAN INTERVAL</div>
                            <div style='color: #a0a0a0; font-size: 0.9rem;'>{status['scan_interval_hours']}h</div>
                        </div>
                        <div>
                            <div style='color: #39FF14; font-size: 0.8rem; font-weight: 600;'>LAST SCAN</div>
                            <div style='color: #a0a0a0; font-size: 0.9rem;'>{last_scan}</div>
                        </div>
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )

def show_vulnerabilities():
    """Show vulnerabilities with enhanced filtering options"""
    st.header(" Vulnerability Browser")
    
    col1, col2, col3, col4 = st.columns(4)
    
    allowed_oems = get_allowed_oems()
    stats_oems = list(st.session_state.db_ops.get_vulnerability_stats(allowed_oems=allowed_oems)['oem_distribution'].keys())
    
    with col1:
        oem_filter = st.selectbox(
            "Filter by OEM",
            ["All"] + stats_oems
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
    
    oem_name = None if oem_filter == "All" else oem_filter
    days = None
    if days_back != "All":
        days = int(days_back.split()[0])
    
    if search_term:
        vulnerabilities = st.session_state.db_ops.search_vulnerabilities(search_term, limit=limit)
    else:
        vulnerabilities = st.session_state.db_ops.get_vulnerabilities(
            oem_name=oem_name,
            severity=None,
            days_back=days,
            allowed_oems=allowed_oems,
            limit=limit * 2
        )
    
    if severity_filter:
        vulnerabilities = [v for v in vulnerabilities if v.severity_level in severity_filter]
    
    if cvss_min > 0:
        vulnerabilities = [v for v in vulnerabilities if v.cvss_score and float(v.cvss_score) >= cvss_min]
    
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
    
    vulnerabilities = vulnerabilities[:limit]
    
    st.subheader(f"Found {len(vulnerabilities)} vulnerabilities")
    
    if vulnerabilities:
        vuln_map = {v.id: v for v in vulnerabilities}
        
        for vuln in vulnerabilities:
            status_color_map = {
                "Open": "#FF073A",
                "Investigating": "#FF9500",
                "Mitigated": "#39FF14",
                "False Positive": "#888888",
                "Assigned": "#00A8CC",
                "Resolved": "#39FF14",
                "Closed": "#555555"
            }
            status_color = status_color_map.get(vuln.status, "#00A8CC")
            
            st.markdown(
                f"""
                <div class="glass-card" style="border-left: 4px solid {status_color}; margin-bottom: 1rem; padding: 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                        <div>
                            <span style="background-color: {status_color}20; color: {status_color}; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; border: 1px solid {status_color}40;">
                                {vuln.status.upper()}
                            </span>
                            <span style="background-color: #333; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; margin-left: 10px; border: 1px solid #444;">
                                {vuln.severity_level.upper()}
                            </span>
                        </div>
                        <div style="color: #666; font-size: 0.9rem; font-family: 'JetBrains Mono', monospace;">
                            {vuln.published_date.strftime('%Y-%m-%d')}
                        </div>
                    </div>
                    <h3 style="margin: 0 0 5px 0; font-family: 'Space Grotesk'; font-size: 1.3rem; color: #fff;">
                        {vuln.product_name} 
                    </h3>
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #39FF14; margin-bottom: 10px;">
                        {vuln.unique_id}
                    </div>
                    <div style="color: #aaa; font-size: 0.9rem; margin-bottom: 10px;">
                        <strong>OEM:</strong> {vuln.oem_name} &nbsp;•&nbsp; 
                        <strong>Version:</strong> {vuln.product_version or 'N/A'} &nbsp;•&nbsp; 
                        <strong>CVSS:</strong> {vuln.cvss_score or 'N/A'}
                    </div>
                    <div style="color: #ddd; font-size: 0.95rem; line-height: 1.5; margin-bottom: 0;">
                        {vuln.vulnerability_description[:200] + '...' if len(vuln.vulnerability_description) > 200 else vuln.vulnerability_description}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            with st.expander(" Manage & Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Full Description:**<br>{vuln.vulnerability_description}", unsafe_allow_html=True)
                
                
                with col2:
                    st.write(f"**Source:** [View Link]({vuln.source_url})" if vuln.source_url else "")


                st.divider()
                
                user = st.session_state.get("user")
                if user and user.organization_id:
                    st.divider()
                    c_assign1, c_assign2 = st.columns([1, 1])
                    with c_assign1:
                        st.markdown("###  Assignment")
                        if vuln.assigned_to:
                            st.info(f"Assigned to: **{vuln.assigned_to.username}**")
                        else:
                            st.write("Unassigned")
                        
                        if user.role in ['Owner', 'Team Lead']:
                            team = st.session_state.db_ops.get_organization_users(user.organization_id)
                            team_map = {u.username: u.id for u in team}
                            
                            assignee_username = st.selectbox(
                                "Assign to:", 
                                list(team_map.keys()), 
                                key=f"assign_select_{vuln.id}",
                                index=None,
                                placeholder="Select team member"
                            )
                            
                            if st.button("Assign", key=f"assign_btn_{vuln.id}"):
                                if assignee_username:
                                    assignee_id = team_map[assignee_username]
                                    if st.session_state.db_ops.assign_vulnerability(vuln.id, assignee_id, user.id):
                                        st.success(f"Task assigned to {assignee_username} and email sent!")
                                        
                                        assignee = next((u for u in team if u.id == assignee_id), None)
                                        if assignee:
                                            st.session_state.email_service.send_assignment_email(
                                                assignee_email=assignee.email,
                                                assignee_name=assignee.username,
                                                assigner_name=user.username,
                                                vulnerability_title=vuln.product_name,
                                                vulnerability_id=vuln.unique_id,
                                                severity=vuln.severity_level
                                            )
                                            
                                        st.rerun()
                                    else:
                                        st.error("Assignment failed. Please check the logs for details.")
                                        logger.error(f"Assignment failed for vuln {vuln.id} to user {assignee_id}")
                                else:
                                    st.warning("Please select a user.")

                st.divider()
                
                st.markdown("### 🔄 Status Management")
                c1, c2 = st.columns([1, 1])
                
                with c1:
                    current_status = vuln.status or "Open"
                    status_options = ["Open", "Assigned", "In Progress", "Resolved", "Mitigated", "False Positive", "Closed"]
                    
                    if current_status not in status_options:
                        status_options.append(current_status)
                        
                    new_status = st.selectbox(
                        "Status", 
                        status_options,
                        key=f"status_{vuln.id}",
                        index=status_options.index(current_status)
                    )
                    
                    if new_status != current_status:
                        st.session_state.db_ops.update_vulnerability_status(
                            vulnerability_id=vuln.id,
                            new_status=new_status,
                            user=user.username if user else "Admin"
                        )
                        st.success(f"Status updated to {new_status}")
                        st.rerun()

                with c2:
                    resolution_note = st.text_area("Resolution Notes", value=vuln.resolution_notes or "", key=f"vuln_note_{vuln.id}", height=100)
                    if st.button("💾 Save Notes", key=f"vuln_save_{vuln.id}"):
                        if st.session_state.db_ops.set_resolution_notes(vuln.id, resolution_note):
                            st.success("Notes saved!")
                        else:
                            st.error("Failed to save notes")

                with st.expander(" Audit Trail"):
                    logs = st.session_state.db_ops.get_audit_logs(vuln.id)
                    if logs:
                        for log in logs:
                            st.text(f"{log.timestamp.strftime('%Y-%m-%d %H:%M')} - {log.user}: {log.action} ({log.old_value} -> {log.new_value})")
                    else:
                        st.caption("No history available.")
    else:
        st.info("No vulnerabilities found matching your criteria.")

def show_subscriptions():
    """Show email and Slack subscription management"""
    st.header(" Email & Slack Subscription Management")
    db_ops = st.session_state.db_ops
    all_subs = db_ops.get_subscriptions()
    if not all_subs:
        st.markdown(
            """
            <div style='background: #262626; border-radius: 12px; border-left: 8px solid #39FF14; padding: 2rem; margin-bottom: 2rem; color: #fff;'>
                <h3 style='color: #39FF14;'>No Subscriptions Yet!</h3>
                <p>For platform email alerts, add a quick test subscription below.
                   <b>Demo suggestion:</b><br>Email: <b>admin@example.com</b>, OEM: <b>Intel</b>, Severities: <b>Critical, High</b></p>
            </div>
            """, unsafe_allow_html=True
        )

    
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
                        if notification_type in ["Email", "Both"]:
                            email_sub = st.session_state.db_ops.add_subscription(
                                email=email,
                                slack_webhook_url=None,
                                oem_name=oem,
                                product_name=product_name if product_name else None,
                                severity_filter=severity_str
                            )
                            st.success(f"Email subscription added successfully! ID: {email_sub.id}")
                        
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
    st.header(" Manual Vulnerability Scan")
    
    st.subheader("Scan All OEMs")
    
    if st.button(" Run Full Scan", type="primary"):

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
                                email_results = st.session_state.email_service.send_bulk_vulnerability_alerts(vuln)
                                if email_results['sent'] > 0:
                                    st.info(f"Sent {email_results['sent']} email notification{'s' if email_results['sent'] != 1 else ''} for {uid}.")
                                total_emails_sent += email_results['sent']
                                
                                slack_results = st.session_state.slack_service.send_bulk_vulnerability_alerts(vuln)
                                if slack_results['sent'] > 0:
                                    st.info(f"Sent {slack_results['sent']} Slack notification{'s' if slack_results['sent'] != 1 else ''} for {uid}.")
                                total_emails_sent += slack_results['sent']

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
                                    email_notif = st.session_state.email_service.send_bulk_vulnerability_alerts(vuln)
                                    emails_sent += email_notif['sent']
                                    if email_notif['sent'] > 0:
                                        st.info(f"Sent {email_notif['sent']} email notification{'s' if email_notif['sent'] != 1 else ''} for {uid}.")
                                    
                                    slack_notif = st.session_state.slack_service.send_bulk_vulnerability_alerts(vuln)
                                    emails_sent += slack_notif['sent']
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
    st.header(" Analytics & Insights")

    
    stats = st.session_state.db_ops.get_vulnerability_stats()
    

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
    
    st.subheader("Vulnerabilities by OEM")
    
    if stats['oem_distribution']:

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
    
        st.subheader("Recent Vulnerability Trends")
    
    recent_vulns = st.session_state.db_ops.get_vulnerabilities(days_back=30, limit=1000)
    
    if recent_vulns:
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
    st.header(" Export Data")

    
    st.subheader("Export Vulnerabilities")
    
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
    
    oem_name = None if export_oem == "All" else export_oem
    severity = None if export_severity == "All" else export_severity
    days = None
    if export_days != "All":
        days = int(export_days.split()[0])
    
    vulnerabilities = st.session_state.db_ops.get_vulnerabilities(
        oem_name=oem_name,
        severity=severity,
        days_back=days,
        limit=10000  
    )
    
    st.info(f"Found {len(vulnerabilities)} vulnerabilities matching your criteria.")
    
    if vulnerabilities:
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv_data = df_export.to_csv(index=False)
            st.download_button(
                label=" Download CSV",

                data=csv_data,
                file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        
        with col2:
            json_data = df_export.to_json(orient='records', indent=2)
            st.download_button(
                label=" Download JSON",

                data=json_data,
                file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col3:
            try:
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name='Vulnerabilities', index=False)
                excel_data = output.getvalue()
                
                st.download_button(
                    label=" Download Excel",

                    data=excel_data,
                    file_name=f"vulnerabilities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.warning("Excel export requires openpyxl. Install with: pip install openpyxl")
        
        st.subheader("Data Preview")
        st.dataframe(df_export.head(10), use_container_width=True)
    
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
                label=" Download Subscriptions CSV",
                data=csv_subs,
                file_name=f"subscriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_subs = df_subs.to_json(orient='records', indent=2)
            st.download_button(
                label=" Download Subscriptions JSON",
                data=json_subs,
                file_name=f"subscriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("No subscriptions found.")

def show_settings():
    """Show settings and configuration"""
    st.header(" Settings & Configuration")

    
    st.subheader("Email Configuration")
    
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
                    if st.session_state.email_service is None:
                        st.session_state.email_service = create_email_service(st.session_state.db_ops)
                    
                    import logging
                    logging.basicConfig(level=logging.INFO)
                    
                    success = st.session_state.email_service.test_email_configuration()
                    
                    if success:
                        st.success("✅ Email configuration test successful! Check your inbox at " + st.session_state.email_service.email_username)
                    else:
                        st.error("❌ Email configuration test failed.")
                        
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
    
    st.subheader("Slack Integration")
    current_webhook = st.session_state.db_ops.get_setting("slack_webhook_url", "")
    new_webhook = st.text_input("Slack Webhook URL", value=current_webhook, type="password")
    
    if new_webhook != current_webhook:
        if st.button("Save Webhook"):
            st.session_state.db_ops.set_setting("slack_webhook_url", new_webhook)
            st.success("Slack Webhook URL saved!")
            
    if st.button("Test Slack Alert"):
        if not new_webhook:
            st.error("Please save a Webhook URL first.")
        else:
            from utils.slack_notifier import send_slack_alert
            
            class MockVuln:
                product_name = "Test Product"
                oem_name = "Test OEM"
                unique_id = "TEST-2024-001"
                severity_level = "Critical"
                vulnerability_description = "This is a test alert from the OEM Alert System."
                source_url = "https://example.com"
            
            if send_slack_alert(MockVuln(), new_webhook):
                st.success("Test alert sent successfully!")
            else:
                st.error("Failed to send test alert.")

    user = st.session_state.user
    if user and user.role in ['Owner', 'Team Lead'] and user.organization_id:
        st.divider()
        st.subheader(" Team Management")
        
        with st.expander("Invite New Member"):
            with st.form("invite_form"):
                invite_email = st.text_input("Email Address")
                invite_role = st.selectbox("Role", ["Analyst", "Team Lead"])
                
                if st.form_submit_button("Send Invitation"):
                    if st.session_state.db_ops.get_user_by_email(invite_email):
                        st.error("User with this email already exists.")
                    else:
                        invite = st.session_state.db_ops.create_invitation(invite_email, user.organization_id, invite_role)
                        if invite:
                            invite_link = f"http://localhost:8501/?token={invite.token}"
                            
                            if st.session_state.email_service.send_invitation_email(invite_email, invite_link, invite_role):
                                st.success(f"Invitation sent to {invite_email}")
                            else:
                                st.warning(f"Invitation created but email failed. Share this link: {invite_link}")
                        else:
                            st.error("Failed to create invitation.")

        st.write("Current Team Members")
        team_members = st.session_state.db_ops.get_organization_users(user.organization_id)
        if team_members:
            team_data = [{
                "Username": u.username,
                "Email": u.email,
                "Role": u.role,
                "Joined": u.created_at.strftime('%Y-%m-%d')
            } for u in team_members]
            st.dataframe(pd.DataFrame(team_data), use_container_width=True)
    
    if user and user.role in ['Owner'] and user.organization_id:
        st.divider()
        st.subheader(" Organization Settings")
        
        st.write("### Managed Data Sources")
        st.info("Select which OEMs are relevant to your organization. Analysts will only see vulnerabilities from selected OEMs.")
        
        all_oems = get_all_oems()
        all_oem_ids = list(all_oems.keys())
        
        org = st.session_state.db_ops.get_organization(user.organization_id)
        
        current_selection = []
        if org and org.enabled_oems:
            if org.enabled_oems == "ALL":
                current_selection = all_oem_ids
            else:
                current_selection = [x.strip() for x in org.enabled_oems.split(",") if x.strip() in all_oem_ids]
        else:
             current_selection = all_oem_ids

        selected_oems = st.multiselect(
            "Active OEM Sources", 
            options=all_oem_ids, 
            default=current_selection,
            format_func=lambda x: all_oems.get(x, {}).get('name', x)
        )
        
        if st.button("Save Organization Settings"):
            value_to_save = "ALL" if len(selected_oems) == len(all_oem_ids) else selected_oems
            
            if st.session_state.db_ops.update_organization_oems(org.id, value_to_save):
                st.success("Organization settings updated successfully!")
                st.rerun()
            else:
                 st.error("Failed to update settings.")

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
    
    st.subheader("OEM Configuration")
    
    oems_config = get_all_oems()
    
    for oem_id, config in oems_config.items():
        with st.expander(f"{config['name']} - {config['description']}"):
            st.write(f"**Base URL:** {config['base_url']}")
            st.write(f"**Vulnerability URL:** {config['vulnerability_url']}")
            st.write(f"**RSS URL:** {config['rss_url']}")
            st.write(f"**Scan Interval:** {config['scan_interval_hours']} hours")
            st.write(f"**Status:** {'Enabled' if config['enabled'] else 'Disabled'}")
    
    st.subheader("System Information")
    
    st.write(f"**Application Version:** 1.0.0")
    st.write(f"**Database:** Supabase")
    st.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
