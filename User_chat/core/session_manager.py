"""
Session Management Module
Handles user sessions with SQLite persistence
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List
from database.chat import ChatDatabase


class SessionManager:
    """Manage user sessions with database persistence"""

    @staticmethod
    def init_session():
        """Initialize session state variables"""
        defaults = {
            # Authentication
            'authenticated': False,
            'user_id': None,
            'user_name': None,
            'user_type': None,
            'user_department': None,
            'user_degree': None,
            'is_guest': False,
            'is_hr': False,
            'guest_session_id': None,  # Unique ID for THIS guest's visit

            # Chat
            'chatbot': None,
            'messages': [],
            'current_session_id': None,
            'initialized': False,

            # Database
            'chat_db': ChatDatabase(),

            # Conversation
            'suggested_queries': [],
            'interactive_options': {},
            'current_topic': 'general',
            'conversation_stats': {
                'total_messages': 0,
                'user_messages': 0,
                'bot_responses': 0,
                'session_start': datetime.now(),
                'topics_discussed': set()
            }
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @staticmethod
    def login_user(user_data: Dict[str, Any]):
        """Set user session after successful login"""
        import uuid

        st.session_state.authenticated = True
        st.session_state.user_id = user_data['user_id']
        st.session_state.user_name = user_data['name']
        st.session_state.user_type = user_data['user_type']
        st.session_state.user_department = user_data['department']
        st.session_state.user_degree = user_data.get('degree')
        st.session_state.is_hr = user_data.get('is_hr', False)
        st.session_state.is_guest = user_data.get('is_guest', False)

        # Generate unique guest session ID for THIS visit (guests only)
        if st.session_state.is_guest:
            st.session_state.guest_session_id = f"guest_{uuid.uuid4().hex[:12]}"
        else:
            st.session_state.guest_session_id = None

    @staticmethod
    def logout_user():
        """Clear user session"""
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.user_type = None
        st.session_state.user_department = None
        st.session_state.user_degree = None
        st.session_state.is_hr = False
        st.session_state.is_guest = False
        st.session_state.guest_session_id = None  # CRITICAL: Clear guest session ID
        st.session_state.messages = []
        st.session_state.current_session_id = None
        st.session_state.interactive_options = {}
        st.session_state.suggested_queries = []
        st.session_state.initialized = False

    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)

    @staticmethod
    def get_user_info() -> Dict[str, Any]:
        """Get current user info"""
        return {
            'user_id': st.session_state.get('user_id'),
            'user_name': st.session_state.get('user_name'),
            'user_type': st.session_state.get('user_type'),
            'user_department': st.session_state.get('user_department'),
            'user_degree': st.session_state.get('user_degree'),
            'is_hr': st.session_state.get('is_hr', False),
            'is_guest': st.session_state.get('is_guest', False),
            'session_id': st.session_state.get('current_session_id')
        }

    @staticmethod
    def create_new_session() -> str:
        """Create new chat session in database with full user context"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        user_info = SessionManager.get_user_info()

        # Create in database with full context
        db = st.session_state.chat_db
        db.create_session(
            session_id=session_id,
            user_id=user_info['user_id'],
            user_type=user_info['user_type'],
            is_guest=user_info['is_guest'],
            user_name=user_info['user_name'],
            user_department=user_info['user_department'],
            user_degree=user_info['user_degree'],
            guest_session_id=st.session_state.get('guest_session_id')
        )

        # Set as current
        st.session_state.current_session_id = session_id
        st.session_state.messages = []

        # Reset stats
        st.session_state.conversation_stats = {
            'total_messages': 0,
            'user_messages': 0,
            'bot_responses': 0,
            'session_start': datetime.now(),
            'topics_discussed': set()
        }

        return session_id

    @staticmethod
    def save_message(role: str, content: str, timestamp: str, is_suggestion: bool = False,
                    intent: str = None, sentiment: str = None, lead_score: int = None):
        """Save message to database with optional intent/sentiment/lead_score"""
        if not st.session_state.current_session_id:
            return

        # Save to database
        db = st.session_state.chat_db
        db.save_message(
            session_id=st.session_state.current_session_id,
            role=role,
            content=content,
            timestamp=timestamp,
            is_suggestion=is_suggestion,
            intent=intent,
            sentiment=sentiment,
            lead_score=lead_score
        )

        # Update title if first user message (check from database)
        if role == 'user':
            messages = db.get_session_messages(st.session_state.current_session_id)
            # Filter only user messages to count
            user_messages = [m for m in messages if m['role'] == 'user']
            if len(user_messages) == 1:  # This is the first user message
                title = content[:50] + ("..." if len(content) > 50 else "")
                db.update_session_title(st.session_state.current_session_id, title)

    @staticmethod
    def can_access_session(session_id: str) -> bool:
        """Check if current user has permission to access this session"""
        db = st.session_state.chat_db

        # Get session info from database
        try:
            import sqlite3
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_id, user_type, is_guest, guest_session_id
                FROM chat_sessions
                WHERE session_id = ?
            ''', (session_id,))

            result = cursor.fetchone()
            conn.close()

            if not result:
                return False

            session_user_id, session_user_type, session_is_guest, session_guest_id = result

            current_user_id = st.session_state.get('user_id')
            current_is_guest = st.session_state.get('is_guest', False)
            current_guest_session_id = st.session_state.get('guest_session_id')

            # For guest users: Must match guest_session_id
            if current_is_guest:
                return (session_is_guest == 1 and
                        session_guest_id == current_guest_session_id)

            # For authenticated users: Must match user_id and NOT be a guest session
            else:
                return (session_user_id == current_user_id and
                        session_is_guest == 0)

        except Exception as e:
            print(f"Error checking session access: {e}")
            return False

    @staticmethod
    def load_session(session_id: str):
        """Load session from database with security check"""
        # SECURITY: Check if user has permission to access this session
        if not SessionManager.can_access_session(session_id):
            print(f"Access denied to session {session_id}")
            return

        db = st.session_state.chat_db

        # Load messages
        messages = db.get_session_messages(session_id)

        st.session_state.current_session_id = session_id
        st.session_state.messages = messages

        # Recalculate stats
        user_msgs = [m for m in messages if m['role'] == 'user']
        bot_msgs = [m for m in messages if m['role'] == 'assistant']

        st.session_state.conversation_stats = {
            'total_messages': len(messages),
            'user_messages': len(user_msgs),
            'bot_responses': len(bot_msgs),
            'session_start': datetime.now(),
            'topics_discussed': set()
        }

    @staticmethod
    def get_chat_history() -> List[Dict[str, Any]]:
        """Get chat history from database (isolated for guests)"""
        user_info = SessionManager.get_user_info()

        if not user_info['user_id']:
            return []

        db = st.session_state.chat_db

        # Guests see only THEIR sessions from THIS visit
        if user_info['is_guest']:
            guest_session_id = st.session_state.get('guest_session_id')
            if not guest_session_id:
                return []
            sessions = db.get_guest_sessions(guest_session_id)
        else:
            # Authenticated users see all their sessions
            sessions = db.get_user_sessions(user_info['user_id'], user_info['user_type'])

        # Convert created_at/updated_at strings to datetime
        for session in sessions:
            try:
                session['created_at'] = datetime.fromisoformat(session['created_at'])
                session['updated_at'] = datetime.fromisoformat(session['updated_at'])
            except:
                session['created_at'] = datetime.now()
                session['updated_at'] = datetime.now()

        return sessions

    @staticmethod
    def delete_session(session_id: str):
        """Delete session from database with security check"""
        # SECURITY: Check if user has permission to delete this session
        if not SessionManager.can_access_session(session_id):
            print(f"Access denied: Cannot delete session {session_id}")
            return

        db = st.session_state.chat_db
        db.delete_session(session_id)

        # Clear if it was current session
        if st.session_state.current_session_id == session_id:
            st.session_state.current_session_id = None
            st.session_state.messages = []

    @staticmethod
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
