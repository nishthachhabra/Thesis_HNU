"""
Login Page Module
Handles user authentication UI
"""

import streamlit as st
from database.auth import DatabaseAuth
from core.session_manager import SessionManager


def render_login_page():
    """Render the login page"""

    # Cleaner centered header
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0 3rem 0;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>🎓</div>
        <h1 style='color: #1e3a5f; margin: 0;'>HNU Support Chat</h1>
        <p style='color: #6b7280; margin-top: 0.5rem; font-size: 1.1rem;'>AI-Powered Intelligent Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    # User type selection with spacing
    st.markdown("<h3 style='text-align: center; color: #374151; margin-bottom: 2rem;'>Select Your Role</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎓 Student", use_container_width=True, type="primary"):
            st.session_state['login_type'] = 'student'
            st.rerun()

    with col2:
        if st.button("👔 Employee", use_container_width=True, type="primary"):
            st.session_state['login_type'] = 'employee'
            st.rerun()

    with col3:
        if st.button("🤝 Partner", use_container_width=True, type="primary"):
            # Partners don't need login - guest mode
            guest_data = {
                'user_id': 'guest_partner',
                'name': 'Partner Guest',
                'user_type': 'partner',
                'department': 'N/A',
                'degree': None,
                'is_hr': False,
                'is_guest': True
            }
            SessionManager.login_user(guest_data)
            st.rerun()

    # Admin login button - centered and smaller
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔧 Admin Login", use_container_width=True):
            st.session_state['login_type'] = 'admin'
            st.rerun()
        st.caption("*HR department only")

    # Show login form if type selected
    if 'login_type' in st.session_state and st.session_state['login_type']:
        show_login_form(st.session_state['login_type'])


def show_login_form(user_type: str):
    """Display login form for selected user type"""

    st.markdown("<br>", unsafe_allow_html=True)

    # Centered login box
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Info badge
        if user_type == 'admin':
            st.warning("⚠️ HR department credentials required")
        else:
            st.info(f"🔐 Login as {user_type.title()}")

        with st.form(f"login_form_{user_type}", clear_on_submit=False):
            st.markdown(f"### {user_type.title()} Login")

            user_id = st.text_input(
                "User ID",
                placeholder="Enter your user ID",
                key=f"uid_{user_type}"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key=f"pwd_{user_type}"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Buttons
            col1, col2 = st.columns(2)

            with col1:
                login_btn = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")

            with col2:
                back_btn = st.form_submit_button("🔙 Back", use_container_width=True)

            # Guest mode button (only for non-admin)
            if user_type != 'admin':
                guest_btn = st.form_submit_button("👤 Continue as Guest", use_container_width=True)
            else:
                guest_btn = False

            if login_btn:
                handle_login(user_id, password, user_type)

            if guest_btn and user_type != 'admin':
                # Guest mode
                guest_data = {
                    'user_id': f'guest_{user_type}',
                    'name': f'Guest {user_type.title()}',
                    'user_type': user_type,
                    'department': 'Guest',
                    'degree': 'N/A' if user_type == 'student' else None,
                    'is_hr': False,
                    'is_guest': True
                }
                SessionManager.login_user(guest_data)
                st.success("✅ Logged in as Guest")
                st.balloons()
                st.rerun()

            if back_btn:
                if 'login_type' in st.session_state:
                    del st.session_state['login_type']
                st.rerun()


def handle_login(user_id: str, password: str, user_type: str):
    """Handle login authentication"""

    if not user_id or not password:
        st.error("❌ Please enter both User ID and Password")
        return

    db_auth = DatabaseAuth()

    # Authenticate based on user type
    if user_type == 'student':
        user_data = db_auth.authenticate_student(user_id, password)
    elif user_type == 'admin':
        user_data = db_auth.authenticate_employee(user_id, password, require_hr=True)
    else:  # employee
        user_data = db_auth.authenticate_employee(user_id, password, require_hr=False)

    if user_data:
        # Check for HR access error
        if user_data.get('error') == 'not_hr':
            st.error(f"❌ Access Denied: Admin access is restricted to HR department only.")
            st.error(f"Your department: {user_data.get('department')}")
            st.info("💡 You can login as Employee instead")
            return

        # Success
        SessionManager.login_user(user_data)
        st.success(f"✅ Welcome, {user_data['name']}!")
        st.balloons()
        st.rerun()
    else:
        st.error("❌ Invalid User ID or Password")
