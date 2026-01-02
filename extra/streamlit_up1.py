"""
Complete Streamlit UI for Enhanced HNU Chatbot with LangGraph
Full implementation with interactive features, authentication, and multi-turn conversations
"""

import streamlit as st
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import pandas as pd

# Import the enhanced chatbot
try:
    from enhanced_langgraph_chatbot import EnhancedHNUChatbot
    CHATBOT_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Could not import Enhanced HNU Chatbot: {e}")
    st.error("Please ensure enhanced_langgraph_chatbot.py is in the same directory")
    CHATBOT_AVAILABLE = False

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
    # Create a mapping of normalized to original column names
    column_mapping = {}
    for col in df.columns:
        normalized = col.strip().lower()
        column_mapping[col] = normalized
    
    # Rename columns to normalized versions
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
        'login_error': None
    }
    
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
                        st.markdown("""
                        **Common Issues:**
                        1. **User ID:** Case-insensitive (NICH = nich = Nich)
                        2. **Password:** EXACT match required (case-sensitive, no extra spaces)
                        3. **Excel File:** Make sure it's closed and not corrupted
                        4. **Column Names:** Check the detected columns in the sidebar
                        
                        **Your Input:**
                        - User ID (normalized): `{}`
                        - Password length: {} characters
                        """.format(user_id.lower(), len(password)))
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
            <p>🚀 Powered by Advanced LangGraph Workflow | Interactive & Context-Aware</p>
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
    """Process user message through the chatbot"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Add user message
    user_message = {
        "role": "user",
        "content": message,
        "avatar": "👤",
        "timestamp": timestamp,
        "is_suggestion": is_suggestion
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
        
        assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
        
        if assistant_messages:
            response_msg = assistant_messages[-1]
            
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
    """Display chat messages"""
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
        
        st.markdown(f"""
        <div class="interactive-section fade-in">
            <h3 style="margin-top: 0;">👋 {greeting}</h3>
            {dept_info}
            {admin_info}
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

def create_enhanced_sidebar():
    """Create enhanced sidebar with authentication"""
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
            
            # Quick actions based on user type
            if st.session_state.user_type:
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
                        ("🛠 Dashboard", "Admin dashboard"),
                        ("👥 User Management", "Manage users"),
                        ("📊 Analytics", "System analytics"),
                        ("📁 Logs", "View system logs"),
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
    initialize_session_state()
    
    if not CHATBOT_AVAILABLE:
        st.error("❌ Chatbot system unavailable.")
        st.stop()
    
    display_enhanced_header()
    create_enhanced_sidebar()
    
    # Show login form if needed
    if st.session_state.show_login and not st.session_state.authenticated:
        display_login_form(st.session_state.login_user_type)
        return
    
    # Only proceed if authenticated
    if not st.session_state.authenticated:
        st.info("👈 Please select your role from the sidebar to begin")
        
        # Display welcome info
        st.markdown("""
        <div class="interactive-section fade-in">
            <h3>🎓 Welcome to HNU Enhanced Support Chatbot</h3>
            <p style="margin-top: 20px;">
                <strong>Guest Mode Available:</strong> Prospective students and employees can use guest mode for general information.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    display_user_badge()
    
    # Initialize chatbot
    if not st.session_state.initialized:
        with st.spinner("🚀 Initializing Enhanced Chatbot System..."):
            chatbot, error = load_enhanced_chatbot()
            
            if chatbot:
                st.session_state.chatbot = chatbot
                st.session_state.initialized = True
                st.success("✅ System ready! All features activated.")
            else:
                st.error(f"❌ Initialization failed: {error}")
                st.stop()
    
    # Main chat
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
    
    # Stats
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 📊 Session Statistics")
        display_conversation_stats()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; padding: 20px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 15px;'>
        <h4 style="margin: 0; color: #1e293b;">🎓 HNU Enhanced Support Chatbot</h4>
        <p style="margin: 10px 0; font-size: 0.95rem;">
            <strong>Powered by:</strong> Advanced LangGraph Workflows | Multi-turn Conversations
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