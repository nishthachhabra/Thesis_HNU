"""
Vollständige Streamlit UI für erweiterten HNU Chatbot mit LangGraph
Vollständige Implementierung mit interaktiven Funktionen und Mehrrunden-Gesprächen
"""

import streamlit as st
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

# Importiere den erweiterten Chatbot
try:
    from enhance_lang import EnhancedHNUChatbot
    CHATBOT_AVAILABLE = True
except ImportError as e:
    st.error(f"⚠️ Konnte erweiterten HNU Chatbot nicht importieren: {e}")
    st.error("Bitte stellen Sie sicher, dass enhanced_lang.py im selben Verzeichnis ist")
    CHATBOT_AVAILABLE = False

# Seitenkonfiguration
st.set_page_config(
    page_title="HNU Erweiterte Support-Chat",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Erweitertes CSS-Styling
st.markdown("""
    <style>
    /* Haupt-Styling */
    .main { 
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* Chat-Nachrichten-Styling */
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
    
    /* Interaktive Elemente */
    .interactive-section { 
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 20px; 
        border-radius: 15px; 
        margin: 15px 0; 
        border-left: 4px solid #10b981;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .suggested-queries {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid #f59e0b;
    }
    
    /* Kopfzeilen-Styling */
    .main-header {
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a8f 50%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
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
    
    /* Seitenleisten-Styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1e3a5f 0%, #2d5a8f 100%);
        color: white;
    }
    
    /* Button-Styling */
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
    
    /* Interaktive Button-Varianten */
    .quick-action-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    }
    
    .info-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    }
    
    .warning-btn {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
    }
    
    .danger-btn {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
    }
    
    /* Benutzertyp-Badge */
    .user-badge {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Studenten-Badge spezifisches Styling */
    .user-badge.student {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    /* Mitarbeiter-Badge spezifisches Styling */
    .user-badge.employee {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    }
    
    /* Partner-Badge spezifisches Styling */
    .user-badge.partner {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    
    /* Workflow-Debug-Info */
    .workflow-debug {
        background: rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    /* Statistik-Styling */
    .stats-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 15px 0;
    }
    
    /* Animations-Klassen */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Lade-Animation */
    .loading-dots {
        display: inline-block;
    }
    
    .loading-dots::after {
        content: '';
        animation: loading 1.5s infinite;
    }
    
    @keyframes loading {
        0%, 33% { content: '●○○'; }
        34%, 66% { content: '○●○'; }
        67%, 100% { content: '○○●'; }
    }
    
    /* Responsives Design */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 2rem; }
        .main-header p { font-size: 1rem; }
        .stButton>button { padding: 8px 16px; }
    }
    </style>
""", unsafe_allow_html=True)

# Initialisiere Session State mit erweiterten Funktionen
def initialize_session_state():
    """Initialisiere alle Session State Variablen"""
    defaults = {
        'chatbot': None,
        'messages': [],
        'user_type': None,
        'initialized': False,
        'session_id': f"sitzung_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
        'current_topic': 'allgemein',
        'topic_depth': 0,
        'awaiting_response': False,
        'auto_suggestions_enabled': True,
        'theme_mode': 'erweitert',
        'last_interaction': datetime.now(),
        'user_type_changed': False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def load_enhanced_chatbot():
    """Lade den erweiterten Chatbot mit Fehlerbehandlung"""
    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        chatbot = EnhancedHNUChatbot(openai_api_key=openai_key)
        return chatbot, None
    except Exception as e:
        return None, str(e)

def update_conversation_stats(message_type: str, topic: str = None):
    """Aktualisiere Gesprächsstatistiken"""
    stats = st.session_state.conversation_stats
    stats['total_messages'] += 1
    
    if message_type == 'user':
        stats['user_messages'] += 1
    elif message_type == 'assistant':
        stats['bot_responses'] += 1
    
    if topic and topic != 'allgemein':
        stats['topics_discussed'].add(topic)
    
    st.session_state.last_interaction = datetime.now()

def display_enhanced_header():
    """Zeige die erweiterte Kopfzeile an"""
    st.markdown("""
    <div class="main-header fade-in">
        <h1>🎓 HNU Erweiterte Support-Chatbot</h1>
        <p>🚀 Angetrieben durch fortgeschrittene LangGraph-Workflows | Interaktiv & Kontextbewusst</p>
    </div>
    """, unsafe_allow_html=True)

def display_user_badge():
    """Zeige Benutzertyp-Badge mit korrektem Styling an"""
    if st.session_state.user_type:
        user_icons = {"employee": "👔", "student": "🎓", "partner": "🤝"}
        
        icon = user_icons.get(st.session_state.user_type, "👤")
        
        # Deutsche Benutzertyp-Namen
        user_type_names = {
            "employee": "Mitarbeiter",
            "student": "Student",
            "partner": "Partner"
        }
        
        display_name = user_type_names.get(st.session_state.user_type, st.session_state.user_type)
        
        st.markdown(f"""
        <div class="user-badge {st.session_state.user_type} fade-in">
            <strong>{icon} Aktuelle Rolle: {display_name}</strong>
        </div>
        """, unsafe_allow_html=True)

def display_conversation_stats():
    """Zeige Gesprächsstatistiken an"""
    stats = st.session_state.conversation_stats
    duration = datetime.now() - stats['session_start']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("👤 Ihre Nachrichten", stats['user_messages'])
    
    with col2:
        st.metric("🤖 Bot-Antworten", stats['bot_responses'])
    
    with col3:
        st.metric("📊 Besprochene Themen", len(stats['topics_discussed']))
    
    # Sitzungsdauer
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    st.info(f"⏱️ Sitzungsdauer: {hours:02d}:{minutes:02d} | Sitzungs-ID: {st.session_state.session_id}")

def display_interactive_buttons(interactive_options: Dict[str, Any]):
    """Zeige interaktive Buttons an"""
    if not interactive_options.get("buttons"):
        return
    
    st.markdown("---")
    st.markdown("### 🎯 Interaktive Optionen")
    
    # Wörterbuch für Button-Textübersetzungen (Englisch -> Deutsch)
    button_translations = {
        "Continue Topic": "Thema fortsetzen",
        "Change Topic": "Thema wechseln",
        "IT Support": "IT-Support",
        "Room Booking": "Raumbuchung",
        "HR Services": "HR-Services",
        "Library Services": "Bibliotheksservices",
        "Academic Support": "Akademische Unterstützung",
        "Enrollment": "Einschreibung",
        "Partnership": "Partnerschaft",
        "Collaboration": "Zusammenarbeit",
        "Contact Support": "Support kontaktieren",
        "Get Information": "Informationen erhalten",
        "Apply Now": "Jetzt bewerben",
        "Book Now": "Jetzt buchen",
        "View Details": "Details ansehen",
        "Exit": "Beenden",
        "Back": "Zurück",
        "Next": "Weiter",
        "Yes": "Ja",
        "No": "Nein",
        "More Information": "Mehr Informationen",
        "Contact": "Kontakt"
    }
    
    # Erstelle dynamische Spalten basierend auf Anzahl der Buttons
    buttons = interactive_options["buttons"]
    num_buttons = len(buttons)
    
    if num_buttons <= 3:
        cols = st.columns(num_buttons)
    else:
        # Erstelle mehrere Reihen für mehr Buttons
        cols = st.columns(3)
    
    for idx, button_info in enumerate(buttons):
        col_idx = idx % len(cols)
        
        with cols[col_idx]:
            # Übersetze Button-Text ins Deutsche falls verfügbar
            original_text = button_info["text"]
            german_text = button_translations.get(original_text, original_text)
            
            # Übersetze auch die Aktion für den Tooltip
            action_translations = {
                "continue_topic": "Thema fortsetzen",
                "change_topic": "Thema wechseln",
                "contact": "Kontaktieren",
                "booking": "Buchen",
                "application": "Bewerben",
                "information": "Informationen"
            }
            
            action_text = action_translations.get(button_info["action"], button_info["action"])
            
            # Bestimme Button-Stil basierend auf Aktion
            style_class = ""
            action_lower = button_info["action"].lower()
            if "kontakt" in action_lower or "contact" in action_lower:
                style_class = "info-btn"
            elif "bewerbung" in action_lower or "application" in action_lower:
                style_class = "quick-action-btn"
            elif "beenden" in action_lower or "exit" in action_lower or "ändern" in action_lower or "change" in action_lower:
                style_class = "warning-btn"
            
            button_key = f"btn_{button_info['action']}_{idx}_{st.session_state.session_id}"
            
            if st.button(
                german_text, 
                key=button_key,
                use_container_width=True,
                help=f"Klicken für: {action_text}"
            ):
                process_button_click(button_info)

def process_button_click(button_info: Dict[str, str]):
    """Verarbeite Button-Klick und generiere Antwort"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Füge Benutzernachricht hinzu (Button-Klick)
    user_message = {
        "role": "user",
        "content": button_info["text"],
        "avatar": "👤",
        "timestamp": timestamp,
        "button_action": True
    }
    st.session_state.messages.append(user_message)
    update_conversation_stats('user')
    
    # Verarbeite durch Chatbot
    button_command = f"BTN:{button_info['action']}"
    
    try:
        # Verwende asynchrone Verarbeitung
        async def process_button_async():
            return await st.session_state.chatbot.process_message(
                button_command,
                st.session_state.user_type,
                st.session_state.session_id
            )
        
        # Führe asynchrone Funktion aus
        result = asyncio.run(process_button_async())
        
        # Extrahiere Assistenten-Antwort
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
            
            # Aktualisiere interaktive Elemente
            st.session_state.interactive_options = result.get('interactive_options', {})
            st.session_state.suggested_queries = result.get('suggested_queries', [])
            st.session_state.current_topic = result.get('conversation_topic', 'allgemein')
    
    except Exception as e:
        error_message = {
            "role": "assistant",
            "content": f"❌ Fehler beim Verarbeiten der Button-Aktion: {str(e)}Bitte versuchen Sie es erneut oder kontaktieren Sie den Support unter info@hnu.de",
            "avatar": "🤖",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "error": True
        }
        st.session_state.messages.append(error_message)
    
    st.rerun()

def display_suggested_queries():
    """Zeige vorgeschlagene Fragen mit erweitertem Styling an"""
    if not st.session_state.suggested_queries:
        return
    
    st.markdown("---")
    st.markdown("### 💡 Vorgeschlagene Fragen")
    
    # Gruppiere Vorschläge in Reihen
    suggestions = st.session_state.suggested_queries[:6]  # Begrenze auf 6 Vorschläge
    
    for i in range(0, len(suggestions), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(suggestions):
                suggestion = suggestions[i + j]
                
                with col:
                    suggestion_key = f"vorschlag_{i+j}_{st.session_state.session_id}"
                    
                    if st.button(
                        f"💬 {suggestion}", 
                        key=suggestion_key,
                        use_container_width=True,
                        help="Klicken, um diese Frage zu stellen"
                    ):
                        # Verarbeite Vorschlag als reguläre Nachricht
                        process_user_message(suggestion, is_suggestion=True)

def process_user_message(message: str, is_suggestion: bool = False):
    """Verarbeite Benutzernachricht durch den Chatbot"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Füge Benutzernachricht hinzu
    user_message = {
        "role": "user",
        "content": message,
        "avatar": "👤",
        "timestamp": timestamp,
        "is_suggestion": is_suggestion
    }
    st.session_state.messages.append(user_message)
    update_conversation_stats('user')
    
    # Verarbeite durch Chatbot
    try:
        async def process_async():
            return await st.session_state.chatbot.process_message(
                message,
                st.session_state.user_type,
                st.session_state.session_id
            )
        
        # Zeige Verarbeitungsindikator
        with st.spinner("🤖 Verarbeite Ihre Nachricht..."):
            result = asyncio.run(process_async())
        
        # Extrahiere Antwort
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
                "topic": result.get('conversation_topic'),
                "workflow_step": result.get('workflow_step')
            }
            
            st.session_state.messages.append(bot_message)
            update_conversation_stats('assistant', result.get('conversation_topic'))
            
            # Aktualisiere Session State
            st.session_state.interactive_options = result.get('interactive_options', {})
            st.session_state.suggested_queries = result.get('suggested_queries', [])
            st.session_state.current_topic = result.get('conversation_topic', 'allgemein')
            st.session_state.awaiting_response = result.get('awaiting_response', False)
        
        else:
            # Keine Antwort generiert
            error_message = {
                "role": "assistant",
                "content": "Entschuldigung, ich konnte keine passende Antwort generieren. Bitte formulieren Sie Ihre Frage um oder kontaktieren Sie unser Support-Team.",
                "avatar": "🤖",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "error": True
            }
            st.session_state.messages.append(error_message)
    
    except Exception as e:
        # Fehlerbehandlung
        error_message = {
            "role": "assistant",
            "content": f"❌ Es ist ein Fehler aufgetreten: {str(e)}Bitte versuchen Sie es erneut oder kontaktieren Sie den Support unter info@hnu.de für Hilfe.",
            "avatar": "🤖",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "error": True
        }
        st.session_state.messages.append(error_message)
    
    st.rerun()

def display_chat_messages():
    """Zeige Chat-Nachrichten mit erweitertem Styling an"""
    if not st.session_state.messages:
        st.markdown("""
        <div class="interactive-section fade-in">
            <h3 style="margin-top: 0;">👋 Willkommen beim HNU Erweiterten Support!</h3>
            <p>Ich bin Ihr intelligenter Assistent, angetrieben durch fortgeschrittene LangGraph-Workflows. Ich kann Ihnen helfen mit:</p>
            <ul>
                <li>🎓 <strong>Studiengänge:</strong> Bachelor- und Master-Programminformationen</li>
                <li>👔 <strong>Mitarbeiterservices:</strong> IT-Support, HR-Services, Raumbuchung</li>
                <li>📚 <strong>Studentenservices:</strong> Einschreibung, Bibliothek, akademische Unterstützung</li>
                <li>🤝 <strong>Partnerschaft:</strong> Kooperationsmöglichkeiten und Partnerschaften</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Zeige Nachrichten an
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])
            
            # Zeige Workflow-Debug-Info wenn aktiviert
            if (st.session_state.workflow_debug and 
                message["role"] == "assistant" and 
                not message.get("error", False)):
                
                with st.expander("🔍 Workflow-Debug-Info", expanded=False):
                    debug_info = f"""
                    **Absicht:** {message.get('intent', 'N/A')}  
                    **Konfidenz:** {message.get('confidence', 0):.2f}  
                    **Thema:** {message.get('topic', 'N/A')}  
                    **Workflow-Schritt:** {message.get('workflow_step', 'N/A')}
                    """
                    st.markdown(debug_info)
            
            # Zeige Zeitstempel
            if "timestamp" in message:
                st.caption(f"⏰ {message['timestamp']}")

def create_enhanced_sidebar():
    """Erstelle erweiterte Seitenleiste mit allen Steuerelementen"""
    with st.sidebar:
        # Logo und Titel
        st.markdown("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">🎓 HNU Support</h2>
            <p style="color: #e2e8f0; margin: 5px 0 0 0; font-size: 0.9rem;">Erweiterter KI-Assistent</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Benutzertyp-Auswahl
        st.markdown("### 👤 Wählen Sie Ihre Rolle")
        user_type_options = {
            "👔 Mitarbeiter": "employee",
            "🎓 Student": "student", 
            "🤝 Partner": "partner"
        }
        
        # Aktuellen Index basierend auf Benutzertyp erhalten
        current_index = 0
        if st.session_state.user_type in user_type_options.values():
            current_index = list(user_type_options.values()).index(st.session_state.user_type)
        
        selected_type = st.radio(
            "Ich bin ein:",
            options=list(user_type_options.keys()),
            index=current_index,
            help="Wählen Sie Ihre Rolle für personalisierte Unterstützung",
            key="benutzertyp_auswahl"
        )
        
        new_user_type = user_type_options[selected_type]
        
        # Behandle Benutzertypänderungen - KORRIGIERTE LOGIK
        if st.session_state.user_type != new_user_type:
            if st.session_state.user_type is not None and st.session_state.messages:
                # Benutzer ändert Typ und hat bestehende Nachrichten
                st.warning("⚠️ Das Ändern des Benutzertyps löscht den Chat-Verlauf")
                if st.button("✅ Änderung bestätigen", type="primary", key="benutzer_aenderung_bestaetigen"):
                    st.session_state.user_type = new_user_type
                    st.session_state.messages = []
                    st.session_state.interactive_options = {}
                    st.session_state.suggested_queries = []
                    st.session_state.user_type_changed = True
                    st.success(f"✅ Benutzertyp geändert zu {user_type_options[selected_type]}")
                    st.rerun()
            else:
                # Erstmaliges Festlegen des Benutzertyps oder keine Nachrichten zum Löschen
                st.session_state.user_type = new_user_type
                st.session_state.user_type_changed = True
                st.rerun()
        
        st.markdown("---")
        
        
        # Chat-Steuerelemente
        st.markdown("### 💬 Chat-Steuerelemente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Chat löschen", use_container_width=True, key="chat_loeschen_btn"):
                st.session_state.messages = []
                st.session_state.interactive_options = {}
                st.session_state.suggested_queries = []
                st.session_state.conversation_stats['total_messages'] = 0
                st.session_state.conversation_stats['user_messages'] = 0
                st.session_state.conversation_stats['bot_responses'] = 0
                st.session_state.conversation_stats['topics_discussed'] = set()
                st.success("✅ Chat gelöscht!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Neue Sitzung", use_container_width=True, key="neue_sitzung_btn"):
                # Alles außer user_type zurücksetzen
                current_user_type = st.session_state.user_type
                for key in ['messages', 'interactive_options', 'suggested_queries', 'current_topic']:
                    if key in st.session_state:
                        st.session_state[key] = [] if key == 'messages' else {}
                
                # Statistiken zurücksetzen
                st.session_state.conversation_stats = {
                    'total_messages': 0,
                    'user_messages': 0,
                    'bot_responses': 0,
                    'session_start': datetime.now(),
                    'topics_discussed': set()
                }
                
                # Benutzertyp behalten und neue Sitzungs-ID generieren
                st.session_state.user_type = current_user_type
                st.session_state.session_id = f"sitzung_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.success("✅ Neue Sitzung gestartet!")
                st.rerun()
        
        st.markdown("---")
        
        # Systeminformationen
        st.markdown("### ℹ️ Systeminformationen")
        system_info = f"""
        **🌐 Sprachen:** Englisch, Deutsch   
        **⚡ Status:** {'🟢 Online' if st.session_state.initialized else '🔴 Lädt'}
        """
        st.info(system_info)
        
        # Schnellaktionen für jeden Benutzertyp
        if st.session_state.user_type:
            user_type_names = {
                "employee": "Mitarbeiter",
                "student": "Studenten",
                "partner": "Partner"
            }
            
            display_name = user_type_names.get(st.session_state.user_type, st.session_state.user_type)
            
            st.markdown(f"### 🎯 Schnellaktionen für {display_name}")
            
            quick_actions = {
                "employee": [
                    ("💻 IT-Support", "Ich benötige IT-Support"),
                    ("🏢 Raum buchen", "Wie buche ich einen Besprechungsraum?"),
                    ("🔑 Passwort zurücksetzen", "Ich muss mein Passwort zurücksetzen"),
                    ("📞 HR kontaktieren", "HR-Kontaktinformationen")
                ],
                "student": [
                    ("📋 Kurseinschreibung", "Wie schreibe ich mich für Kurse ein?"),
                    ("📜 Zeugnis erhalten", "Ich benötige mein akademisches Zeugnis"),
                    ("📚 Bibliothekszeiten", "Was sind die Öffnungszeiten der Bibliothek?"),
                    ("🎓 Programminfo", "Erzählen Sie mir über Bachelor-Programme")
                ],
                "partner": [
                    ("🤝 Partnerschaft", "Partnerschaftsmöglichkeiten an der HNU"),
                    ("🏛️ Einrichtungen mieten", "Wie miete ich Universitätseinrichtungen"),
                    ("🔬 Forschung", "Optionen für Forschungskooperationen"),
                    ("📅 Veranstaltungsplanung", "Veranstaltungsplanung an der HNU")
                ]
            }
            
            actions = quick_actions.get(st.session_state.user_type, [])
            
            for action_text, action_query in actions:
                action_key = f"schnell_{st.session_state.user_type}_{action_text.replace(' ', '_')}"
                if st.button(action_text, key=action_key, use_container_width=True):
                    process_user_message(action_query, is_suggestion=True)
        
        st.markdown("---")
        
        # Nützliche Links
        st.markdown("### 🔗 Nützliche Links")
        links_html = """
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
            <a href="https://www.hnu.de" target="_blank" style="color: #60a5fa; text-decoration: none;">🌐 HNU-Website</a><br>
            <a href="https://www.hnu.de/studium/bachelor" target="_blank" style="color: #60a5fa; text-decoration: none;">🎓 Bachelor-Programme</a><br>
            <a href="https://www.hnu.de/studium/master" target="_blank" style="color: #60a5fa; text-decoration: none;">📚 Master-Programme</a><br>
            <a href="https://www.hnu.de/bewerbung" target="_blank" style="color: #60a5fa; text-decoration: none;">📝 Bewerbungsportal</a><br>
            <a href="mailto:info@hnu.de" style="color: #60a5fa; text-decoration: none;">📧 Support kontaktieren</a>
        </div>
        """
        st.markdown(links_html, unsafe_allow_html=True)

def main():
    """Haupt-Streamlit-Anwendung"""
    # Initialisiere Session State
    initialize_session_state()
    
    # Überprüfe ob Chatbot verfügbar ist
    if not CHATBOT_AVAILABLE:
        st.error("❌ Erweitertes Chatbot-System ist nicht verfügbar.")
        st.code("pip install langgraph langchain typing-extensions", language="bash")
        st.stop()
    
    # Zeige Kopfzeile an
    display_enhanced_header()
    
    # Erstelle Seitenleiste
    create_enhanced_sidebar()
    
    # Zeige Benutzer-Badge an - zeigt jetzt den korrekten Benutzertyp
    display_user_badge()
    
    # Initialisiere Chatbot falls nötig
    if not st.session_state.initialized:
        with st.spinner("🚀 Initialisiere erweitertes HNU Chatbot-System..."):
            chatbot, error = load_enhanced_chatbot()
            
            if chatbot:
                st.session_state.chatbot = chatbot
                st.session_state.initialized = True
                st.success("✅ Erweitertes Chatbot-System bereit! Alle Funktionen aktiviert.")
                
                # Zeige Funktionsankündigung
                st.balloons()
                
            else:
                st.error(f"❌ Fehler beim Initialisieren des Chatbots: {error}")
                st.info("Bitte überprüfen Sie Ihre Einrichtung und versuchen Sie es erneut.")
                st.stop()
    
    # Haupt-Chat-Bereich
    st.markdown("### 💬 Unterhaltung")
    
    # Chat-Nachrichten-Container
    chat_container = st.container()
    
    with chat_container:
        display_chat_messages()
    
    # Interaktive Buttons-Sektion
    if st.session_state.interactive_options:
        display_interactive_buttons(st.session_state.interactive_options)
    
    # Vorgeschlagene Fragen-Sektion
    if st.session_state.auto_suggestions_enabled and st.session_state.suggested_queries:
        display_suggested_queries()
    
    # Chat-Eingabe
    if st.session_state.user_type:
        # Erweiterte Chat-Eingabe mit Platzhalter
        user_type_prompts = {
            "employee": "Fragen Sie nach IT-Support, Raumbuchung, HR-Services...",
            "student": "Fragen Sie nach Programmen, Einschreibung, Bibliotheksservices...", 
            "partner": "Fragen Sie nach Partnerschaften, Kooperationen, Veranstaltungen..."
        }
        
        placeholder = user_type_prompts.get(st.session_state.user_type, "Geben Sie hier Ihre Nachricht ein...")
        
        if prompt := st.chat_input(placeholder, key="erweiterte_chat_eingabe"):
            process_user_message(prompt)
    
    else:
        st.warning("⚠️ Bitte wählen Sie Ihren Benutzertyp in der Seitenleiste aus, um mit dem Chatten zu beginnen!")
    
    # Gesprächsstatistiken
    if st.session_state.messages:
        st.markdown("---")
        st.markdown("### 📊 Gesprächsstatistiken")
        display_conversation_stats()
    
    # Fußzeile
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; padding: 30px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border-radius: 15px; margin-top: 20px;'>
        <h4 style="margin: 0; color: #1e293b;">🎓 HNU Erweiterte Support-Chatbot</h4>
        <p style="margin: 10px 0; font-size: 0.95rem;">
            <strong>Angetrieben durch:</strong> Fortgeschrittene LangGraph-Workflows | Mehrrunden-Gespräche | Kontextbewusstsein
        </p>
        <p style="margin: 0; font-size: 0.85rem;">
            <strong>Notfallkontakt:</strong> 
            <a href="mailto:info@hnu.de" style="color: #3b82f6;">info@hnu.de</a> | 
            <a href="tel:+49-731-9762-0" style="color: #3b82f6;">+49-731-9762-0</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()