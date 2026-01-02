"""
Chat-Seite Modul
Erweiterte Chat-Oberfläche mit SQLite-Speicherung
"""

import streamlit as st
import asyncio
from datetime import datetime
from core.chatbot import EnhancedHNUChatbot
from core.session_manager import SessionManager
import os
from dotenv import load_dotenv

# Umgebungsvariablen aus übergeordnetem Verzeichnis laden
env_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(env_path)


def render_chat_page():
    """Rendert die erweiterte Chat-Seite mit Datenbank-Speicherung"""

    user_info = SessionManager.get_user_info()

    # Kopfzeile mit Logout
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #1e3a5f 0%, #2d5a8f 50%, #3b82f6 100%);
                    padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;'>
            <h2 style='color: white; margin: 0;'>💬 Naina - HNU Support Chat</h2>
            <p style='color: #e2e8f0; margin: 5px 0 0 0;'>
                {user_info['user_name']} | {user_info['user_type'].title()}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.write("")
        st.write("")
        if st.button("🚪 Abmelden", help="Abmelden"):
            SessionManager.logout_user()
            # URL-Parameter löschen
            if 'auth' in st.query_params:
                del st.query_params['auth']
            if 'session' in st.query_params:
                del st.query_params['session']
            st.rerun()

    # Chatbot initialisieren
    if not st.session_state.get('initialized'):
        with st.spinner("🚀 Chatbot wird initialisiert..."):
            try:
                openai_key = os.environ.get('OPENAI_API_KEY')
                chatbot = EnhancedHNUChatbot(openai_api_key=openai_key)
                st.session_state.chatbot = chatbot
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"❌ Chatbot konnte nicht initialisiert werden: {e}")
                return

    # Seitenleiste mit Chatverlauf
    render_sidebar()

    # Chat-Nachrichten anzeigen
    display_chat_messages()

    # Eingabefeld am unteren Rand
    if prompt := st.chat_input("Nachricht eingeben..."):
        process_user_message(prompt)


def render_sidebar():
    """Rendert die Seitenleiste mit Chatverlauf aus der Datenbank"""

    with st.sidebar:
        st.markdown("### 💬 Chatverlauf")

        # Neuer Chat Button
        if st.button("➕ Neuer Chat", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.session_state.current_session_id = None
            st.session_state.interactive_options = {}
            st.session_state.suggested_queries = []

            if 'session' in st.query_params:
                del st.query_params['session']

            st.rerun()

        st.markdown("---")

        # Chatverlauf für den aktuellen Benutzer abrufen
        chat_history = SessionManager.get_chat_history()

        if chat_history:
            st.caption(f"{len(chat_history)} Unterhaltung(en)")

            for chat in chat_history:
                is_current = chat['session_id'] == st.session_state.get('current_session_id')

                col1, col2 = st.columns([4, 1])

                with col1:
                    button_label = f"💬 **{chat['title']}**" if is_current else f"💬 {chat['title']}"

                    if st.button(button_label, key=f"chat_{chat['session_id']}", use_container_width=True):
                        if not is_current:
                            SessionManager.load_session(chat['session_id'])
                            st.query_params['session'] = chat['session_id']
                            st.rerun()

                with col2:
                    if st.button("🗑️", key=f"del_{chat['session_id']}", help="Löschen"):
                        SessionManager.delete_session(chat['session_id'])
                        st.rerun()

        else:
            st.info("Noch kein Chatverlauf vorhanden")

        st.markdown("---")

        # Aktuelle Sitzungsinfos
        if st.session_state.current_session_id:
            st.markdown("### 📊 Aktuelle Sitzung")
            stats = st.session_state.conversation_stats
            st.metric("Nachrichten", stats['total_messages'])
            st.caption(f"Sitzungs-ID: {st.session_state.current_session_id[:20]}...")


def display_chat_messages():
    """Zeigt Chat-Nachrichten an"""

    if not st.session_state.messages:
        user_info = SessionManager.get_user_info()
        st.markdown(f"""
        <div style='background: white; padding: 2.5rem; border-radius: 20px;
                    margin: 2rem 0; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <div style='font-size: 3rem; margin-bottom: 1rem;'>👋</div>
            <h2 style='color: #1e3a5f; margin-bottom: 1rem;'>Hallo {user_info['user_name']}!</h2>
            <p style='color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem;'>
                Ich bin dein intelligenter Assistent. Wie kann ich dir heute helfen?
            </p>
            
        </div>
        """, unsafe_allow_html=True)
        return

    # Nachrichten anzeigen
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message.get("avatar", "👤")):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")


def display_suggested_queries_compact():
    """Zeigt empfohlene Fragen als kompakte Auswahlfelder"""

    if not st.session_state.suggested_queries:
        return

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: #f9fafb; padding: 1rem; border-radius: 12px; margin: 1rem 0;'>
        <p style='margin: 0 0 0.5rem 0; color: #6b7280; font-size: 0.875rem; font-weight: 600;'>
            💡 Empfohlene Fragen
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
    """Zeigt interaktive Aktionsschaltflächen mit klarem Design"""

    if not interactive_options.get("buttons"):
        return

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: #eff6ff; padding: 1rem; border-radius: 12px; margin: 1rem 0;'>
        <p style='margin: 0 0 0.5rem 0; color: #1e40af; font-size: 0.875rem; font-weight: 600;'>
            🎯 Schnellaktionen
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
    """Verarbeitet die Benutzernachricht über den Chatbot und speichert sie in der Datenbank"""

    user_info = SessionManager.get_user_info()
    timestamp = datetime.now().strftime("%H:%M:%S")

    if not st.session_state.current_session_id:
        SessionManager.create_new_session()
        if st.session_state.current_session_id:
            st.query_params['session'] = st.session_state.current_session_id

    user_message = {
        "role": "user",
        "content": message,
        "avatar": "👤",
        "timestamp": timestamp,
        "is_suggestion": is_suggestion
    }
    st.session_state.messages.append(user_message)
    SessionManager.update_conversation_stats('user')

    try:
        async def process_async():
            return await st.session_state.chatbot.process_message(
                message,
                user_info['user_type'],
                user_info['user_id'],
                user_info['session_id']
            )

        with st.spinner("🤖 Wird verarbeitet..."):
            result = asyncio.run(process_async())

        user_intent = result.get('current_intent', 'allgemeine_frage')
        user_sentiment = result.get('sentiment', 'neutral')
        user_lead_score = result.get('lead_score', 50)

        SessionManager.save_message('user', message, timestamp, is_suggestion,
                                   intent=user_intent, sentiment=user_sentiment,
                                   lead_score=user_lead_score)

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
            SessionManager.save_message('assistant', response_msg["content"], bot_timestamp, False)

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

            st.session_state.interactive_options = result.get('interactive_options', {})
            st.session_state.suggested_queries = result.get('suggested_queries', [])

    except Exception as e:
        error_timestamp = datetime.now().strftime("%H:%M:%S")
        error_content = f"❌ Fehler: {str(e)}\n\nBitte versuchen Sie es erneut oder kontaktieren Sie den Support."

        error_message = {
            "role": "assistant",
            "content": error_content,
            "avatar": "🤖",
            "timestamp": error_timestamp,
            "error": True
        }
        st.session_state.messages.append(error_message)
        SessionManager.save_message('assistant', error_content, error_timestamp, False)

    st.rerun()
