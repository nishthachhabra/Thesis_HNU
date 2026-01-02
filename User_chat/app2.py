"""
HNU Support Chat - Main Application
Clean modular architecture with session persistence and bilingual support (EN/DE)
"""

import streamlit as st
from core.session_manager import SessionManager
import base64
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NAINA - HNU Support Chat",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- BASE STYLING ---
st.markdown("""
    <style>
    .main {
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
    [data-testid="stSidebarNav"] { display: none; }
    /* Chatbot Language Selector */
    details.chatbot {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 10000;
    }
    details.chatbot > summary {
        list-style: none;
        cursor: pointer;
        width: 96px; 
        height: 96px;
        display: flex;
        align-items: center;
    }
    details.chatbot > summary::-webkit-details-marker { display: none; }
    details.chatbot > summary img {
        width: 100%; 
        height: 100%;
        transition: transform .2s ease;
    }
    details.chatbot[open] > summary img { transform: scale(1.05); }
    .chatbot-text {
        position: fixed;
        bottom: 20px;
        right: 120px;
        z-index: 10000;
        font-size: 16px;
        font-weight: bold;
        color: #333;
        text-shadow: 0 0 4px rgba(255,255,255,0.8);
    }
    .chatbox {
        position: absolute;
        bottom: 110%;
        right: 0;
        background: #fff;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,.2);
        padding: 15px 20px;
        width: 260px;
        text-align: center;
        animation: fadeIn .2s ease;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .chatbox .btn {
        display: inline-block;
        margin: 10px 5px 0 5px;
        padding: 6px 12px;
        border-radius: 8px;
        background: #4CAF50;
        color: #fff; 
        text-decoration: none;
    }
    .chatbox .btn:hover { background: #45a049; }
    </style>
""", unsafe_allow_html=True)


# --- LANGUAGE HANDLING ---
lang_from_url = st.query_params.get("lang")

if lang_from_url in ["en", "de"]:
    st.session_state["lang"] = lang_from_url
elif "lang" not in st.session_state:
    st.session_state["lang"] = None


# --- BACKGROUND HANDLING ---
def set_background(image_file: str):
    """Show image before language selection, white after."""
    if st.session_state.get("lang") is None:
        if os.path.exists(image_file):
            with open(image_file, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{encoded}");
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    transition: background 0.6s ease;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
    else:
        st.markdown("""
            <style>
            .stApp {
                background: white !important;
                background-image: none !important;
                transition: background 0.6s ease;
            }
            </style>
        """, unsafe_allow_html=True)


set_background("websiteUI.png")


# --- CHATBOT LANGUAGE SELECTOR ---
def render_language_selector():
    icon_url = "https://cdn-icons-png.flaticon.com/512/4712/4712100.png"
    st.markdown(
        f"""
        <details class="chatbot">
          <summary title="Select Language">
            <img src="{icon_url}" alt="Chatbot">
          </summary>
          <div class="chatbox">
            <p><b>Which language would you prefer?</b><br/>
            <i>Welche Sprache bevorzugen Sie?</i></p>
            <a class="btn" href="?lang=en" target="_self">English</a>
            <a class="btn" href="?lang=de" target="_self">Deutsch</a>
          </div>
        </details>
        <div class="chatbot-text">Naina-HNUChatbot</div>
        """,
        unsafe_allow_html=True
    )


# --- SESSION PERSISTENCE HELPERS ---
def restore_session_from_query_params():
    try:
        query_params = st.query_params
        if 'auth' in query_params:
            auth_token = query_params['auth']
            try:
                decoded = base64.b64decode(auth_token).decode('utf-8')
                user_data = json.loads(decoded)
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

        if 'session' in query_params and st.session_state.get('authenticated'):
            if st.session_state.get('is_guest'):
                if 'session' in st.query_params:
                    del st.query_params['session']
                return
            session_id = query_params['session']
            if not st.session_state.get('current_session_id') or \
               st.session_state.get('current_session_id') != session_id:
                db = st.session_state.get('chat_db')
                if db and db.session_exists(session_id):
                    SessionManager.load_session(session_id)
    except:
        pass


def save_session_to_query_params():
    if st.session_state.get('authenticated'):
        if st.session_state.get('is_guest'):
            return
        try:
            if not st.query_params.get('auth'):
                user_data = {
                    'user_id': st.session_state.get('user_id'),
                    'user_name': st.session_state.get('user_name'),
                    'user_type': st.session_state.get('user_type'),
                    'user_department': st.session_state.get('user_department'),
                    'user_degree': st.session_state.get('user_degree'),
                    'is_hr': st.session_state.get('is_hr', False),
                    'is_guest': False
                }
                token = base64.b64encode(json.dumps(user_data).encode('utf-8')).decode('utf-8')
                st.query_params['auth'] = token
            current_session = st.session_state.get('current_session_id')
            if current_session:
                if st.query_params.get('session') != current_session:
                    st.query_params['session'] = current_session
            else:
                if 'session' in st.query_params:
                    del st.query_params['session']
        except:
            pass


# --- MAIN APP FLOW ---
def main():
    SessionManager.init_session()
    restore_session_from_query_params()

    # ✅ No language yet → show selector
    if not st.session_state.get("lang"):
        render_language_selector()
        return

    # ✅ Language chosen → import correct modules dynamically
    if st.session_state["lang"] == "en":
        from pages.login import render_login_page
        from User_chat.pages.chat1 import render_chat_page
    else:
        from pages.login_de import render_login_page
        from pages.chat_de import render_chat_page

    # --- LOGIN CHECK & PAGE ROUTING ---
    # Routing logic
    if SessionManager.is_authenticated():
        save_session_to_query_params()
    
        # Check if user is HR/Admin

        if st.session_state.get('is_hr'):
            if st.session_state["lang"] == "en":
                from pages.admin_dashboard import render_admin_dashboard
            else:
                from pages.admin_dashboard_de import render_admin_dashboard
            render_admin_dashboard()
        else:
            render_chat_page()


    else:
        if 'auth' in st.query_params:
            del st.query_params['auth']
        if 'session' in st.query_params:
            del st.query_params['session']
        render_login_page()

    st.caption(f"Language selected: {'English' if st.session_state['lang'] == 'en' else 'Deutsch'}")


if __name__ == "__main__":
    main()
