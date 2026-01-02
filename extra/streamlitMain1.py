"""
Complete Streamlit UI for Enhanced HNU Chatbot with LangGraph
Version 2.0 - With Separate CSV Files per User Type
Full implementation with ML-based analytics, sentiment analysis, intent recognition, and persistent logging
"""

import streamlit as st
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import pandas as pd
import time
import traceback
# Import the enhanced chatbot
try:
    from enhanced_langgraph_chatbot import EnhancedHNUChatbot
    CHATBOT_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Could not import Enhanced HNU Chatbot: {e}")
    st.error("Please ensure enhanced_langgraph_chatbot.py is in the same directory")
    CHATBOT_AVAILABLE = False

# Import analytics modules
try:
    from sentiment_analyzer import SentimentAnalyzer
    from analytics_logger import AnalyticsLogger
    from intent_classifier import IntentClassifier
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Analytics modules not available: {e}")
    st.warning("Running without sentiment analysis and logging features")
    ANALYTICS_AVAILABLE = False

try:
    from admin_dashboard import AdminDashboard
    DASHBOARD_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Admin dashboard module not available: {e}")
    DASHBOARD_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="HNU Enhanced Support Chat",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
    <style>
    /* Main styling */
    .main { 
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* Chat message styling */
    .stChatMessage { 
        background-color: white; 
        border-radius: 15px; 
        padding: 20px; 
        margin: 15px 0; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #1e3a5f;
    }
    
    .user-message { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-left: 4px solid #4f46e5;
    }
    
    .bot-message { 
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border-left: 4px solid #ec4899;
    }
    
    /* Interactive elements */
    .interactive-section { 
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 20px; 
        border-radius: 15px; 
        margin: 15px 0; 
        border-left: 4px solid #10b981;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Login form styling */
    .login-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a8f 50%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: left;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: #e2e8f0;
        margin: 10px 0 0 0;
        font-size: 1.2rem;
    }
    
    /* User badge styling */
    .user-badge {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .user-badge.student {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    .user-badge.employee {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    }
    
    .user-badge.partner {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }

    .user-badge.admin {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    
    .user-badge.guest {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
    }
    
    /* Analytics badge */
    .analytics-badge {
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
        color: white;
        padding: 8px 15px;
        border-radius: 15px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 5px;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Suggested queries */
    .suggested-queries {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid #f59e0b;
    }
    
    /* Error/Warning styling */
    .access-denied {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 4px solid #ef4444;
        margin: 20px 0;
    }
    
    /* Analytics display */
    .analytics-box {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid #3b82f6;
    }
    
    /* File info box */
    .file-info-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 12px;
        border-radius: 10px;
        margin: 8px 0;
        border-left: 3px solid #22c55e;
        font-size: 0.85rem;
    }
    
    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 2rem; }
        .main-header p { font-size: 1rem; }
        .stButton>button { padding: 8px 16px; }
    }
    </style>
""", unsafe_allow_html=True)

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to handle variations in naming
    Converts to lowercase and strips whitespace
    """
    column_mapping = {}
    for col in df.columns:
        normalized = col.strip().lower()
        column_mapping[col] = normalized
    
    df_normalized = df.copy()
    df_normalized.columns = [column_mapping[col] for col in df.columns]
    
    return df_normalized

def get_column_value(row, possible_names: list, default=''):
    """
    Get column value by trying multiple possible column names
    """
    for name in possible_names:
        if name in row.index:
            value = row[name]
            if pd.notna(value):
                return str(value).strip()
    return default

# Load user credentials from appropriate Excel file
@st.cache_data
def load_user_credentials(user_type: str):
    """
    Load user credentials from appropriate Excel file based on user type
    - Students: students.xlsx (with Degree column)
    - Employees: employees.xlsx (without Degree column)
    - Admin: employees.xlsx (HR department only, without Degree column)
    """
    try:
        if user_type == "student":
            filename = 'students.xlsx'
            has_degree = True
        elif user_type in ["employee", "admin"]:
            filename = 'employees.xlsx'
            has_degree = False
        else:
            return {}
        
        # Load the Excel file
        df = pd.read_excel(filename)
        
        # Show actual column names for debugging
        st.sidebar.caption(f"📋 Detected columns: {', '.join(df.columns.tolist())}")
        
        # Normalize column names (lowercase, strip whitespace)
        df = normalize_column_names(df)
        
        # Define possible column name variations
        id_columns = ['id', 'user_id', 'userid', 'employee_id', 'student_id']
        password_columns = ['password', 'pwd', 'pass']
        name_columns = ['name', 'first_name', 'firstname']
        surname_columns = ['surname', 'last_name', 'lastname']
        department_columns = ['department', 'dept', 'departement']
        degree_columns = ['degree', 'program', 'programme', 'course']
        
        # Create a dictionary for quick lookup
        credentials = {}
        
        for idx, row in df.iterrows():
            try:
                # Get values with flexible column matching
                user_id = get_column_value(row, id_columns)
                password = get_column_value(row, password_columns)
                name = get_column_value(row, name_columns)
                surname = get_column_value(row, surname_columns)
                department = get_column_value(row, department_columns)
                
                if not user_id or not password:
                    st.warning(f"⚠️ Row {idx+2}: Missing ID or password, skipping...")
                    continue
                
                user_id_lower = user_id.lower()
                full_name = f"{name} {surname}".strip()
                department_upper = department.upper()
                
                user_data = {
                    'password': password,  # Case sensitive - no modification
                    'name': full_name if full_name else "Unknown User",
                    'department': department_upper if department_upper else "Unknown",
                    'user_type': user_type,
                    'is_hr': department_upper == 'HR'
                }
                
                # Only add degree for students
                if has_degree:
                    degree = get_column_value(row, degree_columns)
                    user_data['degree'] = degree if degree else "Unknown"
                else:
                    user_data['degree'] = None
                
                credentials[user_id_lower] = user_data
                
            except Exception as e:
                st.warning(f"⚠️ Row {idx+2}: Error processing - {str(e)}")
                continue
        
        st.sidebar.success(f"✅ Loaded {len(credentials)} user(s) from {filename}")
        
        return credentials
        
    except FileNotFoundError:
        st.error(f"❌ {filename} file not found!")
        st.info(f"Please ensure {filename} is in the same directory as this script.")
        return {}
    except Exception as e:
        st.error(f"❌ Error loading credentials from {filename}: {e}")
        st.info("💡 Tip: Check if the file is not open in Excel and has the correct format")
        return {}

def authenticate_user(user_id: str, password: str, user_type: str) -> Optional[Dict[str, str]]:
    """
    Authenticate user with case-insensitive ID and case-sensitive password
    For admin: Check if user is from HR department
    Returns user info if authenticated, None otherwise
    """
    credentials = load_user_credentials(user_type)
    
    if not credentials:
        return None
    
    user_id_lower = user_id.strip().lower()
    
    if user_id_lower in credentials:
        user_data = credentials[user_id_lower]
        
        # Case-sensitive password comparison - exact match required
        if password == user_data['password']:
            # For admin access, verify HR department
            if user_type == "admin":
                if user_data.get('is_hr', False):
                    return user_data
                else:
                    # Return special error code for non-HR admin attempt
                    return {'error': 'not_hr', 'department': user_data['department']}
            else:
                return user_data
    
    return None

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'chatbot': None,
        'messages': [],
        'user_type': None,
        'authenticated': False,
        'user_name': None,
        'user_id': None,
        'user_department': None,
        'user_degree': None,
        'is_guest': False,
        'is_hr': False,
        'initialized': False,
        'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'workflow_debug': False,
        'suggested_queries': [],
        'interactive_options': {},
        'conversation_stats': {
            'total_messages': 0,
            'user_messages': 0,
            'bot_responses': 0,
            'session_start': datetime.now(),
            'topics_discussed': set()
        },
        'current_topic': 'general',
        'topic_depth': 0,
        'awaiting_response': False,
        'auto_suggestions_enabled': True,
        'theme_mode': 'enhanced',
        'last_interaction': datetime.now(),
        'user_type_changed': False,
        'exit_to_main': False,
        'pending_user_type': None,
        'show_login': False,
        'login_user_type': None,
        'login_error': None,
        'show_analytics': False,
        'show_query_analytics': False,
        'analytics_view_mode': 'overview',
        'analytics_user_type_filter': 'All Combined',
        'show_file_management': False
    }
    
    # Initialize analytics if available
    if ANALYTICS_AVAILABLE:
        defaults['sentiment_analyzer'] = SentimentAnalyzer()
        defaults['analytics_logger'] = AnalyticsLogger('insights')  # Base filename for separate files
        defaults['intent_classifier'] = IntentClassifier('bot_data/synthetic')
    else:
        defaults['sentiment_analyzer'] = None
        defaults['analytics_logger'] = None
        defaults['intent_classifier'] = None
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def load_enhanced_chatbot():
    """Load the enhanced chatbot with error handling"""
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        chatbot = EnhancedHNUChatbot(openai_api_key=openai_key)
        return chatbot, None
    except Exception as e:
        return None, str(e)

def display_access_denied_message(user_type: str, department: str):
    """Display access denied message for non-HR admin attempts"""
    st.markdown(f"""
    <div class="access-denied fade-in">
        <h2 style="color: #dc2626; margin-top: 0;">🚫 Access Denied</h2>
        <p style="color: #991b1b; font-size: 1.1rem;">
            <strong>Admin access is restricted to HR department only.</strong>
        </p>
        <p style="color: #7f1d1d;">
            Your department: <strong>{department}</strong>
        </p>
        <p style="color: #7f1d1d;">
            You can continue as an <strong>Employee</strong> instead.
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_login_form(user_type: str):
    """Display login form for employees, students, and admin"""
    st.markdown(f"""
    <div class="login-container fade-in">
        <h2 style="color: white; margin-top: 0;">🔐 {user_type.title()} Login</h2>
        <p style="color: #e2e8f0;">Please enter your credentials to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display access denied message if applicable
    if st.session_state.get('login_error') == 'not_hr':
        display_access_denied_message(
            user_type, 
            st.session_state.get('attempted_department', 'Unknown')
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔙 Back to Login", use_container_width=True):
                st.session_state.login_error = None
                st.session_state.attempted_department = None
                st.rerun()
        
        with col2:
            if st.button("👔 Login as Employee", use_container_width=True):
                st.session_state.login_error = None
                st.session_state.attempted_department = None
                st.session_state.login_user_type = "employee"
                st.rerun()
        
        return
    
    # Determine which file to use
    if user_type == "student":
        file_info = "📚 Using: students.xlsx"
        file_icon = "🎓"
    else:
        file_info = "💼 Using: employees.xlsx"
        file_icon = "👔"
        if user_type == "admin":
            file_info += " (HR Department Only)"
            file_icon = "🔧"
    
    st.info(f"{file_icon} {file_info}")
    
    with st.form(f"login_form_{user_type}", clear_on_submit=False):
        st.markdown(f"### Login as {user_type.title()}")
        
        user_id = st.text_input(
            "User ID",
            placeholder="Enter your user ID (case-insensitive)",
            key=f"login_id_{user_type}",
            help="Example: nich, absa"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password (EXACT match required)",
            key=f"login_pwd_{user_type}",
            help="Password is case-sensitive and must match exactly"
        )
        
        if user_type == "admin":
            st.warning("⚠️ Admin access requires HR department credentials")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button(
                "🔓 Login",
                use_container_width=True
            )
        
        with col2:
            if user_type != "admin":
                guest_button = st.form_submit_button(
                    "👤 Guest Mode",
                    use_container_width=True
                )
            else:
                guest_button = False
        
        if submit_button:
            if user_id and password:
                # Show what we're trying to authenticate with
                st.info(f"🔍 Attempting login for ID: '{user_id.lower()}' (normalized)")
                
                user_data = authenticate_user(user_id, password, user_type)
                
                if user_data:
                    # Check for HR access denial
                    if user_data.get('error') == 'not_hr':
                        st.session_state.login_error = 'not_hr'
                        st.session_state.attempted_department = user_data.get('department')
                        st.rerun()
                    else:
                        # Successful authentication
                        st.session_state.authenticated = True
                        st.session_state.user_name = user_data['name']
                        st.session_state.user_id = user_id.lower()
                        st.session_state.user_department = user_data['department']
                        st.session_state.user_degree = user_data.get('degree')
                        st.session_state.user_type = user_type
                        st.session_state.is_hr = user_data.get('is_hr', False)
                        st.session_state.is_guest = False
                        st.session_state.show_login = False
                        st.session_state.login_error = None
                        
                        welcome_msg = f"✅ Welcome back, {user_data['name']}!"
                        if user_type == "admin":
                            welcome_msg += " (Admin Access - HR)"
                        
                        st.success(welcome_msg)
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Invalid User ID or Password. Please try again.")
                    with st.expander("🔍 Troubleshooting Tips"):
                        st.markdown(f"""
                        **Common Issues:**
                        1. **User ID:** Case-insensitive (NICH = nich = Nich)
                        2. **Password:** EXACT match required (case-sensitive, no extra spaces)
                        3. **Excel File:** Make sure it's closed and not corrupted
                        4. **Column Names:** Check the detected columns in the sidebar
                        
                        **Your Input:**
                        - User ID (normalized): `{user_id.lower()}`
                        - Password length: {len(password)} characters
                        """)
            else:
                st.warning("⚠️ Please enter both User ID and Password")
        
        if guest_button and user_type != "admin":
            # Guest mode (not available for admin)
            st.session_state.authenticated = True
            st.session_state.user_name = f"Guest {user_type.title()}"
            st.session_state.user_type = user_type
            st.session_state.is_guest = True
            st.session_state.is_hr = False
            st.session_state.show_login = False
            
            st.info(f"👤 Continuing as Guest {user_type.title()}")
            st.rerun()
    
    st.markdown("---")
    
    if user_type != "admin":
        st.info("💡 **Guest Mode:** Prospective students/employees can continue without login for general information.")
    else:
        st.warning("🔒 **Admin Access:** Only HR department employees can access admin features.")
    
    if st.button("🔙 Back to Role Selection", key="back_btn"):
        st.session_state.show_login = False
        st.session_state.login_error = None
        st.session_state.attempted_department = None
        st.rerun()

def update_conversation_stats(message_type: str, topic: str = None):
    """Update conversation statistics"""
    stats = st.session_state.conversation_stats
    stats['total_messages'] += 1
    
    if message_type == 'user':
        stats['user_messages'] += 1
    elif message_type == 'assistant':
        stats['bot_responses'] += 1
    
    if topic and topic != 'general':
        stats['topics_discussed'].add(topic)
    
    st.session_state.last_interaction = datetime.now()

def exit_to_main():
    """Set session flag and navigate back to main1 page"""
    st.session_state.exit_to_main = True
    
    try:
        st.experimental_set_query_params(page='main1')
    except Exception:
        try:
            st.set_query_params(page='main1')
        except Exception:
            pass
    
    try:
        st.experimental_rerun()
    except Exception:
        st.stop()

def display_enhanced_header():
    """Display the enhanced header with exit button"""
    col_left, col_right = st.columns([9, 1])
    with col_left:
        st.markdown("""
        <div class="main-header fade-in">
            <h1>🎓 HNU Enhanced Support Chatbot</h1>
            <p>🚀 Powered by Advanced LangGraph | ML-Based Analytics | Intent Recognition | Separate CSV Logging</p>
        </div>
        """, unsafe_allow_html=True)
    with col_right:
        if st.button("Exit to Main", key="exit_to_main_btn"):
            exit_to_main()

def display_user_badge():
    """Display user badge with authentication status"""
    if st.session_state.authenticated and st.session_state.user_type:
        user_icons = {
            "employee": "👔",
            "student": "🎓",
            "partner": "🤝",
            "admin": "🔧"
        }
        
        icon = user_icons.get(st.session_state.user_type, "👤")
        badge_class = st.session_state.user_type if not st.session_state.is_guest else "guest"
        
        # Build status text with department and degree info
        status_text = f"{icon} {st.session_state.user_name}"
        
        if not st.session_state.is_guest:
            if st.session_state.user_department:
                status_text += f" | {st.session_state.user_department}"
            
            # Only show degree for students
            if st.session_state.user_degree and st.session_state.user_type == "student":
                status_text += f" | {st.session_state.user_degree}"
            
            if st.session_state.user_type == "admin" and st.session_state.is_hr:
                status_text += " | 🔐 HR Admin"
        else:
            status_text += " (Guest Mode)"
        
        st.markdown(f"""
        <div class="user-badge {badge_class} fade-in">
            <strong>{status_text}</strong>
        </div>
        """, unsafe_allow_html=True)

def process_user_message(message: str, is_suggestion: bool = False):
    """Process user message with ML-based intent and sentiment analysis"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    start_time = time.time()
    
    # Perform sentiment analysis and intent classification
    analytics = None
    intent = "general"
    intent_confidence = 0.0
    intent_description = "General Query"
    
    if ANALYTICS_AVAILABLE and st.session_state.sentiment_analyzer:
        try:
            # Sentiment analysis
            analytics = st.session_state.sentiment_analyzer.full_analysis(
                text=message,
                user_type=st.session_state.user_type,
                language=None
            )
            
            # Intent classification
            if st.session_state.intent_classifier and st.session_state.intent_classifier.loaded:
                intent, intent_confidence = st.session_state.intent_classifier.predict_intent(
                    message, 
                    st.session_state.user_type
                )
                intent_description = st.session_state.intent_classifier.get_intent_description(intent)
            
        except Exception as e:
            st.warning(f"⚠️ Analytics processing error: {e}")
            # Use defaults if analytics fail
            analytics = {
                'sentiment': 'neutral',
                'sentiment_confidence': 0.5,
                'lead_score': 50,
                'bias_level': 'low',
                'bias_score': 0.0,
                'bias_patterns': 'none',
                'bias_mitigation': 'N/A',
                'language': 'en'
            }
    
    # Add user message with analytics
    user_message = {
        "role": "user",
        "content": message,
        "avatar": "👤",
        "timestamp": timestamp,
        "is_suggestion": is_suggestion,
        "analytics": analytics,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "intent_description": intent_description
    }
    st.session_state.messages.append(user_message)
    update_conversation_stats('user')
    
    # Process through chatbot
    try:
        async def process_async():
            return await st.session_state.chatbot.process_message(
                message,
                st.session_state.user_type,
                st.session_state.session_id
            )
        
        with st.spinner("🤖 Processing your message..."):
            result = asyncio.run(process_async())
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
        
        if assistant_messages:
            response_msg = assistant_messages[-1]
            
            # Log to appropriate CSV file based on user type
            if ANALYTICS_AVAILABLE and st.session_state.analytics_logger and analytics:
                try:
                    st.session_state.analytics_logger.log_interaction(
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_id,
                        user_name=st.session_state.user_name,
                        user_type=st.session_state.user_type,
                        is_guest=st.session_state.is_guest,
                        department=st.session_state.user_department,
                        degree=st.session_state.user_degree,
                        query=message,
                        analytics=analytics,
                        intent=intent,
                        intent_confidence=intent_confidence,
                        intent_description=intent_description,
                        response_time_ms=response_time_ms
                    )
                except Exception as e:
                    st.warning(f"⚠️ Logging error: {e}")
            
            bot_message = {
                "role": "assistant",
                "content": response_msg["content"],
                "avatar": "🤖",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "intent": result.get('current_intent'),
                "confidence": result.get('confidence'),
                "topic": result.get('conversation_topic')
            }
            
            st.session_state.messages.append(bot_message)
            update_conversation_stats('assistant', result.get('conversation_topic'))
            
            st.session_state.interactive_options = result.get('interactive_options', {})
            st.session_state.suggested_queries = result.get('suggested_queries', [])
            st.session_state.current_topic = result.get('conversation_topic', 'general')
        
    except Exception as e:
        error_message = {
            "role": "assistant",
            "content": f"❌ Error: {str(e)}Please try again or contact support at info@hnu.de",
            "avatar": "🤖",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "error": True
        }
        st.session_state.messages.append(error_message)
    
    st.rerun()

def display_chat_messages():
    """Display chat messages with analytics"""
    if not st.session_state.messages:
        greeting = f"Hi {st.session_state.user_name}! " if st.session_state.authenticated else "Welcome! "
        
        dept_info = ""
        if not st.session_state.is_guest and st.session_state.user_department:
            if st.session_state.user_type == "student" and st.session_state.user_degree:
                dept_info = f"<p>🏛️ Department: <strong>{st.session_state.user_department}</strong> | 📚 Program: <strong>{st.session_state.user_degree}</strong></p>"
            else:
                dept_info = f"<p>🏛️ Department: <strong>{st.session_state.user_department}</strong></p>"
        
        admin_info = ""
        if st.session_state.user_type == "admin" and st.session_state.is_hr:
            admin_info = "<p style='color: #dc2626;'>🔧 <strong>Admin Mode Active</strong> - Full system access granted</p>"
        
        analytics_status = ""
        if ANALYTICS_AVAILABLE:
            analytics_status = "<p style='color: #059669;'>📊 <strong>ML Analytics Enabled</strong> - Sentiment analysis & intent recognition active</p>"
            analytics_status += f"<p style='color: #3b82f6;'>💾 <strong>Logging:</strong> Your queries saved to <code>insights_{st.session_state.user_type}s.csv</code></p>"
        
        st.markdown(f"""
        <div class="interactive-section fade-in">
            <h3 style="margin-top: 0;">👋 {greeting}</h3>
            {dept_info}
            {admin_info}
            {analytics_status}
            <p>I'm your intelligent assistant powered by advanced LangGraph workflows. How can I help you today?</p>
            <ul>
                <li>🎓 Academic Programs & Courses</li>
                <li>📝 Enrollment & Registration</li>
                <li>💻 IT Support & Services</li>
                <li>📚 Library & Resources</li>
                <li>🏢 Facilities & Room Booking</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])
            
            # Display analytics badges for user messages
            if message["role"] == "user" and message.get("analytics") and ANALYTICS_AVAILABLE:
                analytics = message["analytics"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    sentiment_color = {
                        'positive': '#10b981',
                        'negative': '#ef4444',
                        'neutral': '#6b7280'
                    }.get(analytics['sentiment'], '#6b7280')
                    
                    st.markdown(f"""
                    <span style="background: {sentiment_color}; color: white; padding: 4px 10px; 
                                 border-radius: 10px; font-size: 0.8rem; display: inline-block;">
                        😊 {analytics['sentiment'].title()}
                    </span>
                    """, unsafe_allow_html=True)
                
                with col2:
                    lead_color = '#10b981' if analytics['lead_score'] > 70 else '#f59e0b' if analytics['lead_score'] > 40 else '#6b7280'
                    st.markdown(f"""
                    <span style="background: {lead_color}; color: white; padding: 4px 10px; 
                                 border-radius: 10px; font-size: 0.8rem; display: inline-block;">
                        🎯 Score: {analytics['lead_score']}
                    </span>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <span style="background: #3b82f6; color: white; padding: 4px 10px; 
                                 border-radius: 10px; font-size: 0.8rem; display: inline-block;">
                        🌐 {analytics['language'].upper()}
                    </span>
                    """, unsafe_allow_html=True)
                
                # Display intent badge
                if message.get("intent") and message.get("intent_description"):
                    st.markdown(f"""
                    <span style="background: #8b5cf6; color: white; padding: 4px 10px; 
                                 border-radius: 10px; font-size: 0.8rem; display: inline-block; margin-top: 5px;">
                        🎯 {message.get('intent_description')} ({message.get('intent_confidence', 0)*100:.0f}% conf.)
                    </span>
                    """, unsafe_allow_html=True)
            
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")

def display_suggested_queries():
    """Display suggested queries"""
    if not st.session_state.suggested_queries:
        return
    
    st.markdown("---")
    st.markdown("### 💡 Suggested Questions")
    
    suggestions = st.session_state.suggested_queries[:6]
    
    for i in range(0, len(suggestions), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(suggestions):
                suggestion = suggestions[i + j]
                
                with col:
                    suggestion_key = f"suggest_{i+j}_{st.session_state.session_id}"
                    
                    if st.button(
                        f"💬 {suggestion}", 
                        key=suggestion_key,
                        use_container_width=True
                    ):
                        process_user_message(suggestion, is_suggestion=True)

def display_interactive_buttons(interactive_options: Dict[str, Any]):
    """Display interactive buttons"""
    if not interactive_options.get("buttons"):
        return
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    
    buttons = interactive_options["buttons"]
    num_buttons = len(buttons)
    
    if num_buttons <= 3:
        cols = st.columns(num_buttons)
    else:
        cols = st.columns(3)
    
    for idx, button_info in enumerate(buttons):
        col_idx = idx % len(cols)
        
        with cols[col_idx]:
            button_key = f"btn_{button_info['action']}_{idx}_{st.session_state.session_id}"
            
            if st.button(
                button_info["text"], 
                key=button_key,
                use_container_width=True
            ):
                process_user_message(button_info["text"], is_suggestion=True)

def display_file_management():
    """Display file management for admin"""
    if st.session_state.user_type != "admin" or not ANALYTICS_AVAILABLE:
        return
    
    st.markdown("---")
    st.markdown("### 📁 File Management")
    
    try:
        # Get file info
        file_info = st.session_state.analytics_logger.get_file_info()
        
        # Display file status
        for user_type, info in file_info.items():
            if info.get('exists'):
                if 'error' in info:
                    st.error(f"**{user_type.title()}:** ❌ {info['error']}")
                else:
                    st.markdown(f"""
                    <div class="file-info-box">
                        <strong>📄 {user_type.title()}:</strong> {info.get('filename', 'N/A')}<br>
                        📊 Rows: {info.get('row_count', 0)} | 💾 Size: {info.get('size_kb', 0)} KB<br>
                        🕒 Latest: {info.get('latest_entry', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption(f"**{user_type.title()}:** ⚠️ Not created yet")
        
        st.markdown("")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔧 Repair All", help="Fix all CSV files", use_container_width=True):
                with st.spinner("Repairing CSV files..."):
                    success, messages = st.session_state.analytics_logger.repair_csv()
                    for msg in messages:
                        if '✅' in msg:
                            st.success(msg)
                        elif '⚠️' in msg:
                            st.warning(msg)
                        else:
                            st.info(msg)
        
        with col2:
            if st.button("📥 Export Combined", help="Export all data to single CSV", use_container_width=True):
                with st.spinner("Exporting..."):
                    filename = st.session_state.analytics_logger.export_combined_csv()
                    if filename:
                        st.success(f"✅ Exported to {filename}")
                        
                        # Provide download
                        try:
                            with open(filename, 'r', encoding='utf-8') as f:
                                csv_data = f.read()
                            
                            st.download_button(
                                "📥 Download Combined CSV",
                                csv_data,
                                filename,
                                "text/csv",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"Error reading file: {e}")
                    else:
                        st.error("❌ Export failed")
    
    except Exception as e:
        st.error(f"❌ Error in file management: {e}")

def display_analytics_dashboard():
    """Display comprehensive analytics dashboard with multi-file support"""
    if not ANALYTICS_AVAILABLE or not st.session_state.analytics_logger:
        st.error("❌ Analytics not available")
        return
    
    st.markdown("## 📊 Analytics Dashboard")
    
    # User type selector
    col1, col2 = st.columns([3, 1])
    
    with col1:
        filter_user_type = st.selectbox(
            "Select User Type",
            ["All Combined", "Students", "Employees", "Partners"],
            key="analytics_user_type_filter"
        )
    
    with col2:
        st.markdown("### ")  # Spacing
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Map selection to user_type
    user_type_map = {
        "All Combined": None,
        "Students": "student",
        "Employees": "employee",
        "Partners": "partner"
    }
    selected_type = user_type_map[filter_user_type]
    
    # Display summary table
    st.markdown("### 📊 Summary by User Type")
    try:
        summary_df = st.session_state.analytics_logger.get_user_type_summary()
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available yet")
    except Exception as e:
        st.error(f"Error loading summary: {e}")
    
    st.markdown("---")
    
    # Get statistics for selected type
    try:
        stats = st.session_state.analytics_logger.get_statistics(user_type=selected_type)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries", stats.get('total_queries', 0))
        
        with col2:
            st.metric("Unique Users", stats.get('unique_users', 0))
        
        with col3:
            st.metric("Avg Lead Score", f"{stats.get('avg_lead_score', 0):.1f}/100")
        
        with col4:
            st.metric("Intent Confidence", f"{stats.get('avg_intent_confidence', 0)*100:.0f}%")
        
        st.markdown("---")
        
        # View mode selector
        view_mode = st.radio(
            "Select View:",
            ["Overview", "Recent Queries", "User Analytics", "Sentiment Analysis", 
             "Lead Scoring", "Intent Analysis"],
            horizontal=True,
            key="analytics_view_mode"
        )
        
        # Get data for selected user type
        df = st.session_state.analytics_logger.get_insights(
            user_type=selected_type, 
            limit=1000, 
            combine_all=(selected_type is None)
        )
        
        # Display based on view mode
        if view_mode == "Overview":
            st.markdown("### 📈 Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Sentiment Distribution")
                sentiment_dist = stats.get('sentiment_distribution', {})
                if sentiment_dist:
                    df_sentiment = pd.DataFrame(list(sentiment_dist.items()), 
                                               columns=['Sentiment', 'Count'])
                    st.bar_chart(df_sentiment.set_index('Sentiment'))
                else:
                    st.info("No data available")
            
            with col2:
                st.markdown("#### Language Distribution")
                lang_dist = stats.get('language_distribution', {})
                if lang_dist:
                    df_lang = pd.DataFrame(list(lang_dist.items()), 
                                          columns=['Language', 'Count'])
                    st.bar_chart(df_lang.set_index('Language'))
                else:
                    st.info("No data available")
            
            # Intent distribution
            st.markdown("#### Top Intents")
            intent_dist = stats.get('intent_distribution', {})
            if intent_dist:
                df_intent = pd.DataFrame(list(intent_dist.items()), 
                                        columns=['Intent', 'Count']).head(10)
                st.bar_chart(df_intent.set_index('Intent'))
            else:
                st.info("No intent data available")
            
            # Department distribution (for employees/students)
            if selected_type in ['employee', 'student'] or selected_type is None:
                st.markdown("#### Department Distribution")
                dept_dist = stats.get('department_distribution', {})
                if dept_dist:
                    df_dept = pd.DataFrame(list(dept_dist.items()), 
                                          columns=['Department', 'Count'])
                    st.bar_chart(df_dept.set_index('Department'))
        
        elif view_mode == "Recent Queries":
            st.markdown("### 📝 Recent Queries")
            
            if not df.empty:
                # Add filters
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'sentiment' in df.columns:
                        filter_sentiment = st.selectbox(
                            "Filter by Sentiment",
                            ["All"] + df['sentiment'].unique().tolist()
                        )
                    else:
                        filter_sentiment = "All"
                
                with col2:
                    if 'language' in df.columns:
                        filter_language = st.selectbox(
                            "Filter by Language",
                            ["All"] + df['language'].unique().tolist()
                        )
                    else:
                        filter_language = "All"
                
                with col3:
                    if 'intent' in df.columns:
                        filter_intent = st.selectbox(
                            "Filter by Intent",
                            ["All"] + df['intent'].unique().tolist()[:20]  # Top 20 intents
                        )
                    else:
                        filter_intent = "All"
                
                # Apply filters
                filtered_df = df.copy()
                if filter_sentiment != "All" and 'sentiment' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['sentiment'] == filter_sentiment]
                if filter_language != "All" and 'language' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['language'] == filter_language]
                if filter_intent != "All" and 'intent' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['intent'] == filter_intent]
                
                # Display columns based on user type
                if selected_type == 'student':
                    display_columns = ['timestamp', 'user_name', 'degree', 'query', 
                                     'intent_description', 'sentiment', 'lead_score']
                elif selected_type == 'employee':
                    display_columns = ['timestamp', 'user_name', 'department', 'query', 
                                     'intent_description', 'sentiment', 'lead_score']
                else:
                    display_columns = ['timestamp', 'user_name', 'user_type', 'query', 
                                     'intent_description', 'sentiment', 'lead_score']
                
                # Filter to existing columns
                display_columns = [col for col in display_columns if col in filtered_df.columns]
                
                st.dataframe(
                    filtered_df[display_columns].head(50),
                    use_container_width=True,
                    height=400
                )
                
                st.caption(f"Showing {len(filtered_df.head(50))} of {len(filtered_df)} filtered queries")
                
                # Download button
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    f"📥 Download {filter_user_type} Data",
                    csv,
                    f"insights_{filter_user_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
            else:
                st.info("No queries logged yet for this user type")
        
        elif view_mode == "User Analytics":
            st.markdown("### 👤 User Analytics")
            
            if not df.empty:
                # Top users by query count
                st.markdown("#### Most Active Users")
                if 'user_name' in df.columns:
                    user_counts = df['user_name'].value_counts().head(10)
                    st.bar_chart(user_counts)
                
                # Guest vs Authenticated
                st.markdown("#### Guest vs Authenticated Users")
                if 'is_guest' in df.columns:
                    guest_counts = df['is_guest'].value_counts()
                    guest_df = pd.DataFrame({
                        'Type': ['Authenticated' if not x else 'Guest' for x in guest_counts.index],
                        'Count': guest_counts.values
                    })
                    st.bar_chart(guest_df.set_index('Type'))
                
                # Department analysis (for employees/students)
                if 'department' in df.columns and selected_type in ['employee', 'student']:
                    st.markdown("#### Queries by Department")
                    dept_counts = df[df['department'] != 'N/A']['department'].value_counts().head(10)
                    st.bar_chart(dept_counts)
                
                # Average lead score by user
                if 'user_name' in df.columns and 'lead_score' in df.columns:
                    st.markdown("#### Top Users by Average Lead Score")
                    user_lead = df.groupby('user_name')['lead_score'].mean().sort_values(ascending=False).head(10)
                    st.bar_chart(user_lead)
            else:
                st.info("No data available yet")
        
        elif view_mode == "Sentiment Analysis":
            st.markdown("### 😊 Sentiment Analysis")
            
            if not df.empty and 'sentiment' in df.columns:
                # Sentiment over time
                if 'timestamp' in df.columns:
                    st.markdown("#### Sentiment Trends Over Time")
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    sentiment_over_time = df.groupby([df['timestamp'].dt.date, 'sentiment']).size().unstack(fill_value=0)
                    st.line_chart(sentiment_over_time)
                
                # Sentiment by user type (if combined view)
                if selected_type is None and 'user_type' in df.columns:
                    st.markdown("#### Sentiment Distribution by User Type")
                    sentiment_by_type = pd.crosstab(df['user_type'], df['sentiment'])
                    st.bar_chart(sentiment_by_type)
                
                # Average sentiment confidence
                if 'sentiment_confidence' in df.columns:
                    st.markdown("#### Average Sentiment Confidence")
                    avg_confidence = df.groupby('sentiment')['sentiment_confidence'].mean()
                    st.bar_chart(avg_confidence)
                
                # Show negative sentiment queries
                st.markdown("#### Recent Negative Sentiment Queries")
                negative_df = df[df['sentiment'] == 'negative'].tail(10)
                if not negative_df.empty:
                    display_cols = ['timestamp', 'user_name', 'query', 'sentiment_confidence']
                    display_cols = [col for col in display_cols if col in negative_df.columns]
                    st.dataframe(
                        negative_df[display_cols],
                        use_container_width=True
                    )
                else:
                    st.success("No negative sentiment queries!")
            else:
                st.info("No sentiment data available yet")
        
        elif view_mode == "Lead Scoring":
            st.markdown("### 🎯 Lead Scoring Analysis")
            
            if not df.empty and 'lead_score' in df.columns:
                # Lead score distribution
                st.markdown("#### Lead Score Distribution")
                
                # Create histogram data
                hist_data = df['lead_score'].value_counts().sort_index()
                st.bar_chart(hist_data)
                
                # High-value leads (score > 70)
                st.markdown("#### High-Value Leads (Score > 70)")
                high_leads = df[df['lead_score'] > 70]
                
                if not high_leads.empty:
                    display_cols = ['timestamp', 'user_name', 'user_type', 'query', 
                                   'lead_score', 'sentiment', 'intent_description']
                    display_cols = [col for col in display_cols if col in high_leads.columns]
                    
                    st.dataframe(
                        high_leads[display_cols].sort_values('lead_score', ascending=False).head(20),
                        use_container_width=True
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("High-Value Leads Count", len(high_leads))
                    with col2:
                        st.metric("Percentage", f"{len(high_leads)/len(df)*100:.1f}%")
                else:
                    st.info("No high-value leads yet")
                
                # Lead score by user type (if combined)
                if selected_type is None and 'user_type' in df.columns:
                    st.markdown("#### Average Lead Score by User Type")
                    avg_lead_by_type = df.groupby('user_type')['lead_score'].mean().sort_values(ascending=False)
                    st.bar_chart(avg_lead_by_type)
                
                # Lead score by sentiment
                if 'sentiment' in df.columns:
                    st.markdown("#### Average Lead Score by Sentiment")
                    avg_lead_by_sentiment = df.groupby('sentiment')['lead_score'].mean()
                    st.bar_chart(avg_lead_by_sentiment)
            else:
                st.info("No lead scoring data available yet")
        
        elif view_mode == "Intent Analysis":
            st.markdown("### 🎯 Intent Recognition Analysis")
            
            if not df.empty and 'intent' in df.columns:
                # Top intents
                st.markdown("#### Top Detected Intents")
                intent_counts = df['intent'].value_counts().head(15)
                st.bar_chart(intent_counts)
                
                # Intent by user type (if combined)
                if selected_type is None and 'user_type' in df.columns:
                    st.markdown("#### Intent Distribution by User Type")
                    intent_by_type = pd.crosstab(df['user_type'], df['intent'])
                    # Show top 10 intents only
                    top_intents = df['intent'].value_counts().head(10).index
                    intent_by_type_filtered = intent_by_type[intent_by_type.columns.intersection(top_intents)]
                    st.bar_chart(intent_by_type_filtered)
                
                # Average intent confidence
                if 'intent_confidence' in df.columns:
                    st.markdown("#### Average Intent Confidence by Intent")
                    avg_intent_conf = df.groupby('intent')['intent_confidence'].mean().sort_values(ascending=False).head(15)
                    st.bar_chart(avg_intent_conf)
                    
                    # Overall intent confidence stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg Confidence", f"{df['intent_confidence'].mean()*100:.1f}%")
                    with col2:
                        st.metric("Min Confidence", f"{df['intent_confidence'].min()*100:.1f}%")
                    with col3:
                        st.metric("Max Confidence", f"{df['intent_confidence'].max()*100:.1f}%")
                
                # Low confidence intents
                if 'intent_confidence' in df.columns:
                    st.markdown("#### Low Confidence Intent Predictions (< 50%)")
                    low_conf = df[df['intent_confidence'] < 0.5]
                    if not low_conf.empty:
                        display_cols = ['timestamp', 'query', 'intent_description', 'intent_confidence']
                        display_cols = [col for col in display_cols if col in low_conf.columns]
                        
                        st.dataframe(
                            low_conf[display_cols].head(20),
                            use_container_width=True
                        )
                        st.info(f"Found {len(low_conf)} queries with low intent confidence ({len(low_conf)/len(df)*100:.1f}%)")
                    else:
                        st.success("✅ All intent predictions have high confidence!")
                
                # Intent description examples
                if 'intent_description' in df.columns:
                    st.markdown("#### Intent Examples")
                    # Get one example for each top intent
                    top_intents = df['intent'].value_counts().head(5).index
                    for intent in top_intents:
                        intent_df = df[df['intent'] == intent]
                        if not intent_df.empty:
                            example = intent_df.iloc[0]
                            with st.expander(f"📌 {example.get('intent_description', intent)}"):
                                st.write(f"**Example Query:** {example.get('query', 'N/A')}")
                                st.write(f"**Confidence:** {example.get('intent_confidence', 0)*100:.1f}%")
                                st.write(f"**Count:** {len(intent_df)} queries")
            else:
                st.info("No intent data available yet")
    
    except Exception as e:
        st.error(f"❌ Error loading analytics: {e}")
        import traceback
        st.code(traceback.format_exc())

def create_enhanced_sidebar():
    """Create enhanced sidebar with authentication and analytics"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">🎓 HNU Support</h2>
            <p style="color: #e2e8f0; margin: 5px 0 0 0; font-size: 0.9rem;">Enhanced AI Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.authenticated:
            st.markdown("### 👤 Select Your Role")
            user_type_options = {
                "👔 Employee": "employee",
                "🎓 Student": "student",
                "🤝 Partner": "partner"
            }
            
            selected_type = st.radio(
                "I am a:",
                options=list(user_type_options.keys()),
                help="Select your role"
            )
            
            new_user_type = user_type_options[selected_type]
            
            if st.button("Continue", type="primary", use_container_width=True):
                if new_user_type in ["employee", "student"]:
                    st.session_state.show_login = True
                    st.session_state.login_user_type = new_user_type
                    st.rerun()
                else:
                    # Partner doesn't require login
                    st.session_state.authenticated = True
                    st.session_state.user_type = new_user_type
                    st.session_state.user_name = f"Partner User"
                    st.session_state.is_guest = False
                    st.session_state.is_hr = False
                    st.rerun()
            
            st.markdown("")
            if st.button("🔧 Admin Login", key="admin_btn", use_container_width=True):
                st.session_state.show_login = True
                st.session_state.login_user_type = "admin"
                st.rerun()
            
            st.info("🔒 Admin access restricted to HR department")
        
        else:
            # Logged in controls
            if st.session_state.is_guest:
                st.info(f"👤 Guest Mode: {st.session_state.user_type.title()}")
            else:
                role_display = st.session_state.user_type.title()
                if st.session_state.user_type == "admin":
                    role_display = "🔧 Admin (HR)"
                
                st.success(f"✅ {role_display}")
                st.caption(f"👤 {st.session_state.user_name}")
                
                if st.session_state.user_department:
                    if st.session_state.user_type == "student" and st.session_state.user_degree:
                        st.caption(f"🏛️ {st.session_state.user_department} | 📚 {st.session_state.user_degree}")
                    else:
                        st.caption(f"🏛️ {st.session_state.user_department}")
            
            if st.button("🚪 Logout", use_container_width=True):
                # Reset authentication
                st.session_state.authenticated = False
                st.session_state.user_name = None
                st.session_state.user_id = None
                st.session_state.user_type = None
                st.session_state.user_department = None
                st.session_state.user_degree = None
                st.session_state.is_guest = False
                st.session_state.is_hr = False
                st.session_state.messages = []
                st.session_state.interactive_options = {}
                st.session_state.suggested_queries = []
                st.session_state.login_error = None
                st.session_state.show_analytics = False
                st.rerun()
            
            st.markdown("---")
            
            # Chat controls
            st.markdown("### 💬 Chat Controls")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.interactive_options = {}
                    st.session_state.suggested_queries = []
                    st.success("✅ Chat cleared!")
                    st.rerun()
            
            with col2:
                if st.button("🔄 New", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.interactive_options = {}
                    st.session_state.suggested_queries = []
                    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.success("✅ New session!")
                    st.rerun()
            
            st.markdown("---")
            
            # Analytics section for admin
            if st.session_state.user_type == "admin" and st.session_state.is_hr and ANALYTICS_AVAILABLE:
                st.markdown("### 📊 Analytics Dashboard")
                
                if st.button("📈 View Analytics", use_container_width=True, type="primary"):
                    st.session_state.show_analytics = not st.session_state.show_analytics
                    st.rerun()
                
                try:
                    stats = st.session_state.analytics_logger.get_statistics()
                    
                    st.metric("Total Queries", stats.get('total_queries', 0))
                    st.metric("Unique Users", stats.get('unique_users', 0))
                    st.metric("Avg Lead Score", f"{stats.get('avg_lead_score', 0):.1f}/100")
                    st.metric("Intent Confidence", f"{stats.get('avg_intent_confidence', 0)*100:.0f}%")
                    
                except Exception as e:
                    st.error(f"Error loading stats: {e}")
                
                # File management
                display_file_management()
            
            # Quick actions based on user type
            if st.session_state.user_type:
                st.markdown("---")
                st.markdown(f"### 🎯 Quick Actions")
                
                quick_actions = {
                    "employee": [
                        ("💻 IT Support", "I need IT support"),
                        ("🏢 Room Booking", "Book a meeting room"),
                        ("🔑 Password Reset", "Reset my password")
                    ],
                    "student": [
                        ("📋 Enrollment", "Course enrollment help"),
                        ("📚 Library", "Library services"),
                        ("🎓 Programs", "Program information")
                    ],
                    "partner": [
                        ("🤝 Partnership", "Partnership info"),
                        ("🏛️ Facilities", "Rent facilities"),
                        ("🔬 Research", "Research collaboration")
                    ],
                    "admin": [
                        ("👥 User Management", "Manage users"),
                        ("📊 System Analytics", "System analytics"),
                        ("📁 View Logs", "View system logs"),
                        ("🔐 Security", "Security settings")
                    ]
                }
                
                actions = quick_actions.get(st.session_state.user_type, [])
                
                for action_text, action_query in actions:
                    action_key = f"qa_{action_text.replace(' ', '_')}"
                    if st.button(action_text, key=action_key, use_container_width=True):
                        process_user_message(action_query, is_suggestion=True)
        
        st.markdown("---")
        
        # System info
        st.markdown("### ℹ️ System Status")
        status_emoji = '🟢' if st.session_state.initialized else '🔴'
        st.info(f"{status_emoji} {'Online' if st.session_state.initialized else 'Loading'}")
        
        if ANALYTICS_AVAILABLE:
            st.success("📊 ML Analytics: Active")
            if st.session_state.intent_classifier and st.session_state.intent_classifier.loaded:
                st.success("🎯 Intent Recognition: Active")
            else:
                st.warning("🎯 Intent: Fallback Mode")
            st.success("💾 Multi-File Logging: Active")
        else:
            st.warning("📊 Analytics: Disabled")

def display_conversation_stats():
    """Display conversation statistics"""
    stats = st.session_state.conversation_stats
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("👤 Your Messages", stats['user_messages'])
    
    with col2:
        st.metric("🤖 Bot Responses", stats['bot_responses'])
    
    with col3:
        st.metric("📊 Topics", len(stats['topics_discussed']))

def main():
    """Main Streamlit application"""
    import traceback
    
    initialize_session_state()
    
    display_enhanced_header()
    create_enhanced_sidebar()
    
    # ============================================
    # ADMIN DASHBOARD - SHOW ONLY FOR ADMIN/HR
    # ============================================
    if (st.session_state.authenticated and 
        st.session_state.user_type == "admin" and 
        st.session_state.is_hr):
        
        st.markdown("""
        <div class="user-badge admin fade-in">
            <strong>🔧 Admin Dashboard - HR Access</strong>
        </div>
        """, unsafe_allow_html=True)
        
        # Check all requirements
        if DASHBOARD_AVAILABLE and ANALYTICS_AVAILABLE and st.session_state.analytics_logger:
            try:
                dashboard = AdminDashboard(st.session_state.analytics_logger)
                dashboard.render_dashboard()
            except Exception as e:
                st.error(f"❌ Dashboard Error: {e}")
                st.code(traceback.format_exc())
                
                with st.expander("🔍 Debug Information"):
                    st.write("**DASHBOARD_AVAILABLE:**", DASHBOARD_AVAILABLE)
                    st.write("**ANALYTICS_AVAILABLE:**", ANALYTICS_AVAILABLE)
                    st.write("**analytics_logger exists:**", st.session_state.analytics_logger is not None)
                    
                    if st.session_state.analytics_logger:
                        st.write("**CSV File:**", st.session_state.analytics_logger.csv_file)
                        try:
                            import os
                            st.write("**File Exists:**", os.path.exists(st.session_state.analytics_logger.csv_file))
                        except:
                            st.write("**File Exists:**", "Cannot check")
        else:
            st.error("❌ Dashboard requirements not met")
            
            st.markdown("### 🔍 Missing Components:")
            
            issues = []
            if not DASHBOARD_AVAILABLE:
                issues.append("❌ **admin_dashboard.py** not found or has errors")
            else:
                issues.append("✅ admin_dashboard.py loaded")
            
            if not ANALYTICS_AVAILABLE:
                issues.append("❌ **Analytics modules** (sentiment_analyzer.py, analytics_logger.py, intent_classifier.py) not found")
            else:
                issues.append("✅ Analytics modules loaded")
            
            if not st.session_state.analytics_logger:
                issues.append("❌ **AnalyticsLogger** not initialized")
            else:
                issues.append("✅ AnalyticsLogger initialized")
            
            for issue in issues:
                st.markdown(issue)
            
            st.info("""
            **Required Files:**
            - admin_dashboard.py
            - sentiment_analyzer.py
            - analytics_logger.py
            - intent_classifier.py
            - insights.csv (created automatically)
            
            **Install Required:** bash pip install plotly
                    """)
        
        return  # STOP HERE - admin only sees dashboard
    
    # ============================================
    # Show login form if needed (NON-ADMIN)
    # ============================================
    if st.session_state.show_login and not st.session_state.authenticated:
        display_login_form(st.session_state.login_user_type)
        return
    
    # ============================================
    # Only proceed if authenticated (NON-ADMIN)
    # ============================================
    if not st.session_state.authenticated:
        st.info("👈 Please select your role from the sidebar to begin")
        
        # Display welcome info
        analytics_info = ""
        if ANALYTICS_AVAILABLE:
            ml_status = "✅ ML-powered" if (st.session_state.intent_classifier and st.session_state.intent_classifier.loaded) else "⚠️ Fallback mode"
            analytics_info = f"<p style='color: #059669;'><strong>📊 Analytics Enabled ({ml_status}):</strong> All interactions analyzed for sentiment, intent, and logged for insights.</p>"
        
        st.markdown(f"""
        <div class="interactive-section fade-in">
            <h3>🎓 Welcome to HNU Enhanced Support Chatbot</h3>
            {analytics_info}
            <p style="margin-top: 20px;">
                <strong>Features:</strong>
            </p>
            <ul>
                <li>🤖 Advanced LangGraph-powered conversations</li>
                <li>😊 Real-time sentiment analysis</li>
                <li>🎯 ML-based intent recognition</li>
                <li>📊 Comprehensive analytics dashboard (Admin)</li>
                <li>🔐 Secure role-based authentication</li>
            </ul>
            <p style="margin-top: 20px;">
                <strong>Guest Mode Available:</strong> Prospective students and employees can use guest mode for general information.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # ============================================
    # REGULAR USERS: Chat Interface
    # ============================================
    if not CHATBOT_AVAILABLE:
        st.error("❌ Chatbot system unavailable.")
        st.stop()
    
    display_user_badge()
    
    # Initialize chatbot for non-admin users
    if not st.session_state.initialized:
        with st.spinner("🚀 Initializing Enhanced Chatbot System..."):
            chatbot, error = load_enhanced_chatbot()
            
            if chatbot:
                st.session_state.chatbot = chatbot
                st.session_state.initialized = True
                success_msg = "✅ System ready! All features activated."
                if ANALYTICS_AVAILABLE:
                    success_msg += " ML analytics enabled."
                st.success(success_msg)
            else:
                st.error(f"❌ Initialization failed: {error}")
                st.stop()
    
    # Main chat interface
    st.markdown("### 💬 Hey, I am Naina! How can I help you?")
    
    chat_container = st.container()
    with chat_container:
        display_chat_messages()
    
    # Interactive elements
    if st.session_state.interactive_options:
        display_interactive_buttons(st.session_state.interactive_options)
    
    if st.session_state.suggested_queries:
        display_suggested_queries()
    
    # Chat input
    placeholder = "Type your message here..."
    if prompt := st.chat_input(placeholder):
        process_user_message(prompt)
    
    # Show detailed analytics for last query (optional toggle)
    if st.session_state.messages and ANALYTICS_AVAILABLE:
        st.markdown("---")
        
        if st.checkbox("🔍 Show Detailed Query Analytics", value=False, key="show_query_analytics_toggle"):
            last_user_msg = next((msg for msg in reversed(st.session_state.messages) 
                                if msg['role'] == 'user'), None)
            
            if last_user_msg and last_user_msg.get('analytics'):
                analytics = last_user_msg['analytics']
                
                st.markdown("### 📊 Last Query Analysis")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    sentiment_emoji = {
                        'positive': '😊',
                        'negative': '😞',
                        'neutral': '😐'
                    }.get(analytics['sentiment'], '😐')
                    st.metric(
                        f"{sentiment_emoji} Sentiment", 
                        analytics['sentiment'].title(),
                        f"{analytics['sentiment_confidence']*100:.0f}% conf."
                    )
                
                with col2:
                    st.metric("🎯 Lead Score", f"{analytics['lead_score']}/100")
                
                with col3:
                    st.metric("🌐 Language", analytics['language'].upper())
                
                with col4:
                    bias_emoji = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }.get(analytics['bias_level'], '🟢')
                    st.metric(f"{bias_emoji} Bias Level", analytics['bias_level'].title())
                
                # Intent information
                if last_user_msg.get('intent_description'):
                    st.info(f"🎯 **Detected Intent:** {last_user_msg['intent_description']} (Confidence: {last_user_msg.get('intent_confidence', 0)*100:.0f}%)")
                
                # Bias mitigation if needed
                if analytics['bias_level'] != 'low':
                    st.warning(f"⚠️ **Bias Mitigation:** {analytics['bias_mitigation']}")
                    if analytics['bias_patterns'] != 'none':
                        st.info(f"📋 Detected patterns: {analytics['bias_patterns']}")
    
    # Stats
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 📊 Session Statistics")
        display_conversation_stats()
    
    # Footer
    st.markdown("---")
    footer_analytics = ""
    if ANALYTICS_AVAILABLE:
        footer_analytics = "| 📊 ML Analytics | 🎯 Intent Recognition"
    
    st.markdown(f"""
    <div style='text-align: center; color: #64748b; padding: 20px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 15px;'>
        <h4 style="margin: 0; color: #1e293b;">🎓 HNU Enhanced Support Chatbot</h4>
        <p style="margin: 10px 0; font-size: 0.95rem;">
            <strong>Powered by:</strong> Advanced LangGraph Workflows {footer_analytics}
        </p>
        <p style="margin: 0; font-size: 0.85rem;">
            <strong>Emergency Contact:</strong> 
            <a href="mailto:info@hnu.de" style="color: #3b82f6;">info@hnu.de</a> | 
            <a href="tel:+49-731-9762-0" style="color: #3b82f6;">+49-731-9762-0</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()