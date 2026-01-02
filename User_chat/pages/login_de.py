"""
Login-Seite Modul
Verwaltet die Benutzer-Authentifizierungsoberfläche
"""

import streamlit as st
from database.auth import DatabaseAuth
from core.session_manager import SessionManager


def render_login_page():
    """Rendert die Login-Seite"""

    # Zentrierter Header
    st.markdown("""
    <div style='text-align: center; margin: 2rem 0 3rem 0;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>🎓</div>
        <h1 style='color: #1e3a5f; margin: 0;'>Naina - HNU ChatBot</h1>
        <p style='color: #6b7280; margin-top: 0.5rem; font-size: 1.1rem;'>KI-gestützter Intelligenter Assistent</p>
    </div>
    """, unsafe_allow_html=True)

    # Benutzerrollenauswahl
    st.markdown("<h3 style='text-align: center; color: #374151; margin-bottom: 2rem;'>Wählen Sie Ihre Rolle</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🎓 Studierende/r", use_container_width=True, type="primary"):
            st.session_state['login_type'] = 'student'
            st.rerun()

    with col2:
        if st.button("👔 Mitarbeiter/in", use_container_width=True, type="primary"):
            st.session_state['login_type'] = 'employee'
            st.rerun()

    with col3:
        if st.button("🤝 Partner/in", use_container_width=True, type="primary"):
            # Partner benötigen kein Login – Gastmodus
            guest_data = {
                'user_id': 'guest_partner',
                'name': 'Partner Gast',
                'user_type': 'partner',
                'department': 'N/A',
                'degree': None,
                'is_hr': False,
                'is_guest': True
            }
            SessionManager.login_user(guest_data)
            st.rerun()

    # Admin-Login – zentriert
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔧 Admin-Login", use_container_width=True):
            st.session_state['login_type'] = 'admin'
            st.rerun()
        st.caption("*Nur für Personalabteilung (HR)")

    # Loginformular anzeigen, wenn Typ gewählt
    if 'login_type' in st.session_state and st.session_state['login_type']:
        show_login_form(st.session_state['login_type'])


def show_login_form(user_type: str):
    """Zeigt das Loginformular für den ausgewählten Benutzertyp"""

    st.markdown("<br>", unsafe_allow_html=True)

    # Zentriertes Login-Feld
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Hinweisfeld
        if user_type == 'admin':
            st.warning("⚠️ Zugangsdaten der Personalabteilung erforderlich")
        else:
            st.info(f"🔐 Anmeldung als {user_type.title()}")

        with st.form(f"login_form_{user_type}", clear_on_submit=False):
            st.markdown(f"### {user_type.title()} Anmeldung")

            user_id = st.text_input(
                "Benutzer-ID",
                placeholder="Geben Sie Ihre Benutzer-ID ein",
                key=f"uid_{user_type}"
            )

            password = st.text_input(
                "Passwort",
                type="password",
                placeholder="Geben Sie Ihr Passwort ein",
                key=f"pwd_{user_type}"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Buttons
            col1, col2 = st.columns(2)

            with col1:
                login_btn = st.form_submit_button("🔓 Anmelden", use_container_width=True, type="primary")

            with col2:
                back_btn = st.form_submit_button("🔙 Zurück", use_container_width=True)

            # Gastmodus (nicht für Admin)
            if user_type != 'admin':
                guest_btn = st.form_submit_button("👤 Als Gast fortfahren", use_container_width=True)
            else:
                guest_btn = False

            if login_btn:
                handle_login(user_id, password, user_type)

            if guest_btn and user_type != 'admin':
                # Gastmodus
                guest_data = {
                    'user_id': f'guest_{user_type}',
                    'name': f'Gast {user_type.title()}',
                    'user_type': user_type,
                    'department': 'Gast',
                    'degree': 'N/A' if user_type == 'student' else None,
                    'is_hr': False,
                    'is_guest': True
                }
                SessionManager.login_user(guest_data)
                st.success("✅ Angemeldet als Gast")
                st.balloons()
                st.rerun()

            if back_btn:
                if 'login_type' in st.session_state:
                    del st.session_state['login_type']
                st.rerun()


def handle_login(user_id: str, password: str, user_type: str):
    """Verarbeitet die Benutzeranmeldung"""

    if not user_id or not password:
        st.error("❌ Bitte geben Sie sowohl Benutzer-ID als auch Passwort ein")
        return

    db_auth = DatabaseAuth()

    # Authentifizierung nach Benutzertyp
    if user_type == 'student':
        user_data = db_auth.authenticate_student(user_id, password)
    elif user_type == 'admin':
        user_data = db_auth.authenticate_employee(user_id, password, require_hr=True)
    else:  # Mitarbeiter/in
        user_data = db_auth.authenticate_employee(user_id, password, require_hr=False)

    if user_data:
        # HR-Zugriffsprüfung
        if user_data.get('error') == 'not_hr':
            st.error("❌ Zugriff verweigert: Admin-Zugang ist nur für die Personalabteilung (HR) erlaubt.")
            st.error(f"Ihre Abteilung: {user_data.get('department')}")
            st.info("💡 Sie können sich stattdessen als Mitarbeiter/in anmelden")
            return

        # Erfolg
        SessionManager.login_user(user_data)
        st.success(f"✅ Willkommen, {user_data['name']}!")
        st.balloons()
        st.rerun()
    else:
        st.error("❌ Ungültige Benutzer-ID oder Passwort")
