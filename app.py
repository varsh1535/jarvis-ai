import streamlit as st
import bcrypt
import os
import base64
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except:
    Groq = None

st.set_page_config(page_title="Jarvis AI", layout="wide")

# ================= DATABASE =================
class DB:
    def __init__(self):
        self.db = MongoClient("mongodb://localhost:27017/")["jarvis"]
        self.users = self.db["users"]

    def create(self, email, username, password):
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            return self.users.insert_one({
                "email": email,
                "username": username,
                "password": hashed
            })
        except:
            return None

    def login(self, email, password):
        u = self.users.find_one({"email": email})
        if u and bcrypt.checkpw(password.encode(), u["password"]):
            return u
        return None

db = DB()

# ================= AI =================
def get_ai(prompt, username="User"):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return "API key missing"

    client = Groq(api_key=key)

    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": f"You are Ash, assistant for {username}"},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content

# ================= SESSION =================
defaults = {
    "auth": False,
    "username": "",
    "user_id": None,
    "login_success": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= ANIMATED BACKGROUND =================
def animated_bg():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg,#0f172a,#1e1b4b,#020617,#1e293b);
        background-size: 400% 400%;
        animation: gradientMove 12s ease infinite;
    }
    @keyframes gradientMove {
        0% {background-position:0% 50%;}
        50% {background-position:100% 50%;}
        100% {background-position:0% 50%;}
    }
    </style>
    """, unsafe_allow_html=True)

# ================= VIDEO BACKGROUND =================
def video_bg():
    import base64

    try:
        with open("background.mp4", "rb") as f:
            video_bytes = f.read()
        video_base64 = base64.b64encode(video_bytes).decode()

        st.markdown(f"""
        <style>
        /* Remove default background */
        .stApp {{
            background: transparent !important;
        }}

        /* VIDEO BACKGROUND */
        #bg-video {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            z-index: -2;
        }}

        /* DARK OVERLAY */
        #overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.6);
            z-index: -1;
        }}
        </style>

        <video autoplay muted loop id="bg-video">
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>

        <div id="overlay"></div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Video error: {e}")
# ================= LOGIN =================
def login_page():
    animated_bg()

    st.markdown("## 🤖 Jarvis AI")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        with st.form("login"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")

            if st.form_submit_button("Login"):
                user = db.login(email, pwd)
                if user:
                    st.session_state.auth = True
                    st.session_state.username = user["username"]
                    st.session_state.user_id = str(user["_id"])
                    st.session_state.login_success = True
                    st.rerun()
                else:
                    st.error("Invalid login")

    with tab2:
        with st.form("signup"):
            u = st.text_input("Username")
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")

            if st.form_submit_button("Signup"):
                if db.create(e, u, p):
                    st.success("Account created!")
                else:
                    st.error("User exists")

# ================= CHAT =================
def chat_page():
    from chat_page import show_chat

    video_bg()

    if st.session_state.login_success:
        st.success(f"Welcome {st.session_state.username} 🎉")
        st.session_state.login_success = False

    show_chat(get_ai, db, st.session_state.username, st.session_state.user_id)

# ================= MAIN =================
if not st.session_state.auth:
    login_page()
else:
    chat_page()