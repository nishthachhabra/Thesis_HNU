import streamlit as st
import base64
import subprocess

st.set_page_config(page_title="Website UI", layout="wide")

# --- Language handling ---
lang_from_url = st.query_params.get("lang")
st.session_state.setdefault("lang", None)

# --- If user clicked one of the chatbot buttons ---
if lang_from_url == "en":
    st.session_state["lang"] = "en"
    subprocess.run(["streamlit", "run", "streamlit_response2.py"])
elif lang_from_url == "de":
    st.session_state["lang"] = "de"
    subprocess.run(["streamlit", "run", "streamlit_de1.py"])

# --- If no language selected yet, show main page ---
if not st.session_state["lang"]:
    def set_background(image_file: str):
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
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

    set_background("websiteUI.png")

    icon_url = "https://cdn-icons-png.flaticon.com/512/4712/4712100.png"

    # --- Chatbot UI for language selection ---
    st.markdown(
        f"""
        <style>
        details.chatbot {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
        }}
        details.chatbot > summary {{
            list-style: none;
            cursor: pointer;
            width: 96px; 
            height: 96px;
            display: flex;
            align-items: center;
        }}
        details.chatbot > summary::-webkit-details-marker {{ display: none; }}
        details.chatbot > summary img {{
            width: 100%; 
            height: 100%;
            transition: transform .2s ease;
        }}
        details.chatbot[open] > summary img {{ transform: scale(1.05); }}

        .chatbot-text {{
            position: fixed;
            bottom: 20px;
            right: 120px;
            z-index: 10000;
            font-size: 16px;
            font-weight: bold;
            color: #333;
            text-shadow: 0 0 4px rgba(255,255,255,0.8);
        }}

        .chatbox {{
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
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        .chatbox .btn {{
            display: inline-block;
            margin: 10px 5px 0 5px;
            padding: 6px 12px;
            border-radius: 8px;
            background: #4CAF50;
            color: #fff; 
            text-decoration: none;
        }}
        .chatbox .btn:hover {{ background: #45a049; }}
        </style>

        <details class="chatbot">
          <summary title="Open chat">
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

else:
    st.caption(f"Language selected: {'English' if st.session_state['lang'] == 'en' else 'Deutsch'}")