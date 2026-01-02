"""
HNU Support Chat - Main Application
Clean modular architecture with session persistence
"""

import streamlit as st
from core.session_manager import SessionManager
from pages.login import render_login_page
from pages.chat import render_chat_page
import base64
import json

# Page configuration
st.set_page_config(
    page_title="HNU Support Chat",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    /* Hide sidebar navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)


def restore_session_from_query_params():
    """Restore auth and current session from URL query parameters"""
    try:
        query_params = st.query_params

        # Restore authentication
        if 'auth' in query_params:
            auth_token = query_params['auth']

            try:
                decoded = base64.b64decode(auth_token).decode('utf-8')
                user_data = json.loads(decoded)

                # Restore auth if not already authenticated
                if not st.session_state.get('authenticated'):
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_data.get('user_id')
                    st.session_state.user_name = user_data.get('user_name')
                    st.session_state.user_type = user_data.get('user_type')
                    st.session_state.user_department = user_data.get('user_department')
                    st.session_state.user_degree = user_data.get('user_degree')
                    st.session_state.is_hr = user_data.get('is_hr', False)
                    st.session_state.is_guest = user_data.get('is_guest', False)
            except:
                pass

        # Restore current session_id from URL (authenticated users ONLY, not guests)
        if 'session' in query_params and st.session_state.get('authenticated'):
            # SECURITY: Guests should NEVER restore from URL
            if st.session_state.get('is_guest'):
                # Clear the session param for guests
                if 'session' in st.query_params:
                    del st.query_params['session']
                return

            session_id = query_params['session']

            # Load if no current session OR if different from current
            # This handles both fresh refresh (no current_session_id) and switching sessions
            if not st.session_state.get('current_session_id') or \
               st.session_state.get('current_session_id') != session_id:
                # Load this session from database with security check
                db = st.session_state.get('chat_db')
                if db and db.session_exists(session_id):
                    SessionManager.load_session(session_id)  # Has built-in security check

    except:
        pass


def save_session_to_query_params():
    """Save auth and current session_id to URL (NOT for guests)"""
    if st.session_state.get('authenticated'):
        # SKIP URL params for guest users (they shouldn't persist across visits)
        if st.session_state.get('is_guest'):
            return

        try:
            # Save auth token (authenticated users only)
            if not st.query_params.get('auth'):
                user_data = {
                    'user_id': st.session_state.get('user_id'),
                    'user_name': st.session_state.get('user_name'),
                    'user_type': st.session_state.get('user_type'),
                    'user_department': st.session_state.get('user_department'),
                    'user_degree': st.session_state.get('user_degree'),
                    'is_hr': st.session_state.get('is_hr', False),
                    'is_guest': False  # This will never be true here
                }

                token = base64.b64encode(json.dumps(user_data).encode('utf-8')).decode('utf-8')
                st.query_params['auth'] = token

            # Save current session_id to URL
            current_session = st.session_state.get('current_session_id')
            if current_session:
                # Update URL with current session
                if st.query_params.get('session') != current_session:
                    st.query_params['session'] = current_session
            else:
                # Clear session from URL if no active session
                if 'session' in st.query_params:
                    del st.query_params['session']

        except:
            pass


def main():
    """Main application entry point"""

    # Initialize session
    SessionManager.init_session()

    # Restore session from URL if present
    restore_session_from_query_params()

    # Route to appropriate page
    if SessionManager.is_authenticated():
        # Save auth + session_id to URL for persistence
        save_session_to_query_params()
        render_chat_page()
    else:
        # Clear URL params if logged out
        if 'auth' in st.query_params:
            del st.query_params['auth']
        if 'session' in st.query_params:
            del st.query_params['session']
        render_login_page()


if __name__ == "__main__":
    main()
