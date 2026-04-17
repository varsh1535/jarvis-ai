import streamlit as st
import uuid
from PIL import Image
import pandas as pd
import PyPDF2

def show_chat(get_ai, db=None, username="User", user_id=None):

    # ================= SESSION =================
    if "chats" not in st.session_state:
        st.session_state.chats = {}

    if "current_chat" not in st.session_state:
        cid = str(uuid.uuid4())
        st.session_state.chats[cid] = []
        st.session_state.current_chat = cid

    # ================= FUNCTIONS =================
    def new_chat():
        cid = str(uuid.uuid4())
        st.session_state.chats[cid] = []
        st.session_state.current_chat = cid
        st.rerun()

    def switch(cid):
        st.session_state.current_chat = cid
        st.rerun()

    def delete_chat(cid):
        del st.session_state.chats[cid]
        if st.session_state.chats:
            st.session_state.current_chat = list(st.session_state.chats.keys())[0]
        else:
            new_chat()
        st.rerun()

    def logout():
        st.session_state.clear()
        st.rerun()

    current = st.session_state.chats[st.session_state.current_chat]

    # ================= SIDEBAR =================
    with st.sidebar:
        st.markdown("### ✨ Jarvis AI")
        st.markdown(f"**{username}**  \n🟢 Online")

        if st.button("➕ New Chat"):
            new_chat()

        st.markdown("### Chats")

        for cid, msgs in st.session_state.chats.items():
            col1, col2 = st.columns([4,1])

            label = "New Chat"
            if msgs:
                label = msgs[0]["content"][:20]

            with col1:
                if st.button(label, key=f"chat_{cid}"):
                    switch(cid)

            with col2:
                if st.button("🗑️", key=f"del_{cid}"):
                    delete_chat(cid)

        st.markdown("---")

        if st.button("🚪 Logout"):
            logout()

    # ================= FILE UPLOAD =================
    uploaded_file = st.file_uploader(
        "📎 Upload file",
        type=["pdf", "txt", "csv", "png", "jpg"],
        accept_multiple_files=False
    )

    if uploaded_file:
        file_type = uploaded_file.type

        # 📄 PDF
        if "pdf" in file_type:
            pdf = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

            st.success("PDF uploaded ✅")
            st.write(text[:500])

            response = get_ai(f"Summarize this PDF:\n{text[:2000]}", username)
            current.append({"role": "assistant", "content": response})

        # 📝 TEXT
        elif "text" in file_type:
            content = uploaded_file.read().decode("utf-8")
            st.write(content[:500])

            response = get_ai(f"Analyze this text:\n{content}", username)
            current.append({"role": "assistant", "content": response})

        # 📊 CSV
        elif "csv" in file_type:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)

            response = get_ai(f"Analyze this dataset:\n{df.head().to_string()}", username)
            current.append({"role": "assistant", "content": response})

        # 🖼️ IMAGE
        elif "image" in file_type:
            img = Image.open(uploaded_file)
            st.image(img)

            response = get_ai("Describe this image", username)
            current.append({"role": "assistant", "content": response})

    # ================= CHAT =================
    for m in current:
        if m["role"] == "user":
            st.markdown(f"<div style='text-align:right;background:#6366f1;padding:10px;border-radius:15px;margin:10px;color:white'>{m['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:left;background:#1e293b;padding:10px;border-radius:15px;margin:10px;color:#ddd'>{m['content']}</div>", unsafe_allow_html=True)

    # ================= INPUT =================
    prompt = st.chat_input("Message Ash...")

    if prompt:
        current.append({"role": "user", "content": prompt})

        response = get_ai(prompt, username)

        current.append({"role": "assistant", "content": response})

        # 💾 SAVE TO DB
        if db and user_id:
            try:
                db.messages.insert_one({
                    "user_id": user_id,
                    "prompt": prompt,
                    "response": response
                })
            except:
                pass

        st.rerun()