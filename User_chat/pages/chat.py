"""
Chat Page Module
Enhanced chat interface with SQLite persistence
"""

import streamlit as st
import asyncio
from datetime import datetime
from core.chatbot import EnhancedHNUChatbot
from core.session_manager import SessionManager
import os
from dotenv import load_dotenv

# Load environment variables from parent directory
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)


def render_chat_page():
    """Render the enhanced chat page with database persistence"""

    user_info = SessionManager.get_user_info()

    # Header with logout
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #1e3a5f 0%, #2d5a8f 50%, #3b82f6 100%);
                    padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;'>
            <h2 style='color: white; margin: 0;'>💬 HNU Support Chat</h2>
            <p style='color: #e2e8f0; margin: 5px 0 0 0;'>
                {user_info['user_name']} | {user_info['user_type'].title()}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", help="Logout"):
            SessionManager.logout_user()
            # Clear URL params before rerun
            if 'auth' in st.query_params:
                del st.query_params['auth']
            if 'session' in st.query_params:
                del st.query_params['session']
            st.rerun()

    # Initialize chatbot
    if not st.session_state.get('initialized'):
        with st.spinner("🚀 Initializing chatbot..."):
            try:
                openai_key = os.environ.get('OPENAI_API_KEY')
                chatbot = EnhancedHNUChatbot(openai_api_key=openai_key)
                st.session_state.chatbot = chatbot
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Failed to initialize chatbot: {e}")
                return

    # Render sidebar with chat history from database
    render_sidebar()

    # Display chat messages
    display_chat_messages()

    # Chat input (fixed at bottom)
    if prompt := st.chat_input("Type your message..."):
        process_user_message(prompt)

    # Interactive elements - ONLY show if there are messages
    if st.session_state.messages:
        if st.session_state.get('suggested_queries'):
            display_suggested_queries_compact()

        if st.session_state.get('interactive_options'):
            display_interactive_buttons_clean(st.session_state['interactive_options'])


def render_sidebar():
    """Render sidebar with chat history from database"""

    with st.sidebar:
        st.markdown("### 💬 Chat History")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            # Clear current chat
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.session_state.interactive_options = {}
            st.session_state.suggested_queries = []

            # Clear session from URL immediately
            if 'session' in st.query_params:
                del st.query_params['session']

            st.rerun()

        st.markdown("---")

        # Get chat history from database for THIS user only
        chat_history = SessionManager.get_chat_history()

        if chat_history:
            st.caption(f"{len(chat_history)} conversation(s)")

            for chat in chat_history:
                is_current = chat['session_id'] == st.session_state.get('current_session_id')

                col1, col2 = st.columns([4, 1])

                with col1:
                    # Highlight current session
                    button_label = f"💬 **{chat['title']}**" if is_current else f"💬 {chat['title']}"

                    if st.button(button_label, key=f"chat_{chat['session_id']}", use_container_width=True):
                        if not is_current:
                            # Load this session from database
                            SessionManager.load_session(chat['session_id'])

                            # Update URL immediately with new session
                            st.query_params['session'] = chat['session_id']

                            st.rerun()

                with col2:
                    if st.button("🗑️", key=f"del_{chat['session_id']}", help="Delete"):
                        SessionManager.delete_session(chat['session_id'])
                        st.rerun()

        else:
            st.info("No chat history yet")

        st.markdown("---")

        # Current session info
        if st.session_state.current_session_id:
            st.markdown("### 📊 Current Session")
            stats = st.session_state.conversation_stats
            st.metric("Messages", stats['total_messages'])
            st.caption(f"Session ID: {st.session_state.current_session_id[:20]}...")


def display_chat_messages():
    """Display chat messages"""

    if not st.session_state.messages:
        user_info = SessionManager.get_user_info()
        st.markdown(f"""
        <div style='background: white; padding: 2.5rem; border-radius: 20px;
                    margin: 2rem 0; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>👋</div>
            <h2 style='color: #1e3a5f; margin-bottom: 1rem;'>Hi {user_info['user_name']}!</h2>
            <p style='color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem;'>
                I'm your intelligent assistant. How can I help you today?
            </p>
            
        </div>
        """, unsafe_allow_html=True)
        return

    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar", "👤")):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")


def display_suggested_queries_compact():
    """Display suggested questions as compact pills"""

    if not st.session_state.suggested_queries:
        return

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: #f9fafb; padding: 1rem; border-radius: 12px; margin: 1rem 0;'>
        <p style='margin: 0 0 0.5rem 0; color: #6b7280; font-size: 0.875rem; font-weight: 600;'>
            💡 Suggested Questions
        </p>
    </div>
    """, unsafe_allow_html=True)

    suggestions = st.session_state.suggested_queries[:4]

    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions):
        col_idx = idx % 2
        with cols[col_idx]:
            if st.button(suggestion, key=f"suggest_{idx}", use_container_width=True):
                process_user_message(suggestion, is_suggestion=True)


def display_interactive_buttons_clean(interactive_options):
    """Display interactive action buttons with clean design"""

    if not interactive_options.get("buttons"):
        return

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: #eff6ff; padding: 1rem; border-radius: 12px; margin: 1rem 0;'>
        <p style='margin: 0 0 0.5rem 0; color: #1e40af; font-size: 0.875rem; font-weight: 600;'>
            🎯 Quick Actions
        </p>
    </div>
    """, unsafe_allow_html=True)

    buttons = interactive_options["buttons"][:3]
    cols = st.columns(len(buttons))

    for idx, button_info in enumerate(buttons):
        with cols[idx]:
            if st.button(button_info["text"], key=f"btn_{idx}", use_container_width=True, type="secondary"):
                process_user_message(button_info["text"], is_suggestion=True)


def process_user_message(message: str, is_suggestion: bool = False):
    """Process user message through chatbot and save to database"""

    user_info = SessionManager.get_user_info()
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Create new session if this is first message
    if not st.session_state.current_session_id:
        SessionManager.create_new_session()

        # Update URL immediately with new session
        if st.session_state.current_session_id:
            st.query_params['session'] = st.session_state.current_session_id

    # Add user message to session state
    user_message = {
        "role": "user",
        "content": message,
        "avatar": "👤",
        "timestamp": timestamp,
        "is_suggestion": is_suggestion
    }
    st.session_state.messages.append(user_message)
    SessionManager.update_conversation_stats('user')

    # Process through chatbot FIRST to get intent/sentiment
    try:
        async def process_async():
            return await st.session_state.chatbot.process_message(
                message,
                user_info['user_type'],
                user_info['user_id'],
                user_info['session_id']
            )

        with st.spinner("🤖 Processing..."):
            result = asyncio.run(process_async())

        # Extract intent/sentiment from result
        user_intent = result.get('current_intent', 'general_query')
        user_sentiment = result.get('sentiment', 'neutral')
        user_lead_score = result.get('lead_score', 50)

        # NOW save user message with intent/sentiment
        SessionManager.save_message('user', message, timestamp, is_suggestion,
                                   intent=user_intent, sentiment=user_sentiment,
                                   lead_score=user_lead_score)

        # Extract bot response
        assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]

        if assistant_messages:
            response_msg = assistant_messages[-1]
            bot_timestamp = datetime.now().strftime("%H:%M:%S")

            bot_message = {
                "role": "assistant",
                "content": response_msg["content"],
                "avatar": "🤖",
                "timestamp": bot_timestamp
            }

            st.session_state.messages.append(bot_message)
            SessionManager.update_conversation_stats('assistant', result.get('conversation_topic'))

            # Save bot response to database
            SessionManager.save_message('assistant', response_msg["content"], bot_timestamp, False)

            # Update user stats with analysis results (for backward compatibility)
            if result.get('analysis_result'):
                from database.chat import ChatDatabase
                chat_db = ChatDatabase()
                chat_db.update_user_stats(
                    user_id=user_info['user_id'],
                    user_type=user_info['user_type'],
                    intent=user_intent,
                    sentiment=user_sentiment,
                    lead_score=user_lead_score
                )

            # Update interactive elements
            st.session_state.interactive_options = result.get('interactive_options', {})
            st.session_state.suggested_queries = result.get('suggested_queries', [])

    except Exception as e:
        error_timestamp = datetime.now().strftime("%H:%M:%S")
        error_content = f"❌ Error: {str(e)}\n\nPlease try again or contact support."

        error_message = {
            "role": "assistant",
            "content": error_content,
            "avatar": "🤖",
            "timestamp": error_timestamp,
            "error": True
        }
        st.session_state.messages.append(error_message)

        # Save error to database too
        SessionManager.save_message('assistant', error_content, error_timestamp, False)

    st.rerun()
