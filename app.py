import streamlit as st
import pandas as pd
import io
from docx import Document
from datetime import datetime
from db import create_user, authenticate_user, add_comment, get_comment_by_passcode, list_comments_for_user
from nlp_backend import predict_sentiment, summarize_text, load_models

# ---------------------------
# Streamlit page config
# ---------------------------
st.set_page_config(page_title="MCA E-Consultation Portal", layout="wide")

# ---------------------------
# Light theme styling
# ---------------------------
st.markdown("""
<style>
.reportview-container { background: #f7fbff; }
.stButton>button {
    background-color: #0b66c3;
    color: white;
    border-radius: 6px;
    font-weight: 500;
}
.stDownloadButton>button {
    background-color: #2b8a3e;
    color: white;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Header
# ---------------------------
st.image("https://upload.wikimedia.org/wikipedia/commons/4/4f/Emblem_of_India.svg", width=60)
st.title("🇮🇳 Ministry of Corporate Affairs — E-Consultation Portal")
st.caption("Smart India Hackathon 2025 | AI-Powered Sentiment Analysis System")

# ---------------------------
# Session state initialization
# ---------------------------
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

# ---------------------------
# Sidebar login/register
# ---------------------------
st.sidebar.header("User Access")

if st.session_state.user_id is None:
    action = st.sidebar.radio("Select", ["Login", "Register", "Guest"])

    if action == "Register":
        u = st.sidebar.text_input("Username")
        p = st.sidebar.text_input("Password", type="password")
        m = st.sidebar.text_input("Mobile (optional)")
        if st.sidebar.button("Create Account"):
            ok, msg = create_user(u, p, m)
            st.sidebar.success(msg if ok else msg)

    elif action == "Login":
        u = st.sidebar.text_input("Username")
        p = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            ok, val = authenticate_user(u, p)
            if ok:
                st.session_state.user_id = val
                st.session_state.username = u
                st.sidebar.success("Logged in successfully!")
            else:
                st.sidebar.error(val)

    else:
        st.sidebar.info("You are using guest mode (limited access).")

else:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.experimental_rerun()

# ---------------------------
# Load NLP models (optional)
# ---------------------------
use_nlp = st.sidebar.checkbox("Enable full NLP models (slower)", value=False)
if use_nlp:
    with st.spinner("Loading NLP models..."):
        load_models()

# ---------------------------
# Main action selection
# ---------------------------
SECTORS = [
    "Agriculture", "Mining and quarrying", "Manufacturing",
    "Electricity and gas", "Construction", "Trade",
    "Transport", "Business service"
]

page = st.radio("Choose Action", ["Submit Comment", "Track Complaint"], horizontal=True)

# ---------------------------
# Submit Comment Page
# ---------------------------
if page == "Submit Comment":
    st.subheader("✍️ Submit a New Comment")
    sector = st.selectbox("Select Sector", SECTORS)
    comment = st.text_area("Enter your comment", height=150, placeholder="Type feedback, complaint or suggestion...")

    if st.button("Submit Comment"):
        if not comment.strip():
            st.error("Please enter a valid comment!")
        else:
            sentiment, score = predict_sentiment(comment, use_model=use_nlp)
            summary = summarize_text(comment, use_model=use_nlp)
            user_id = st.session_state.user_id if st.session_state.user_id else 0
            code = add_comment(user_id, sector, comment, sentiment, summary)

            st.success(f"✅ Comment submitted successfully! Your tracking passcode: `{code}`")
            st.info(f"**Sentiment:** {sentiment.capitalize()} | **Summary:** {summary}")

# ---------------------------
# Track Complaint Page
# ---------------------------
elif page == "Track Complaint":
    st.subheader("🔎 Track your Complaint")
    code = st.text_input("Enter your passcode to check status")

    if st.button("Track"):
        record = get_comment_by_passcode(code.strip())
        if not record:
            st.error("❌ No record found for this passcode.")
        else:
            st.success("✅ Record found!")
            st.write(f"**Sector:** {record['sector']}")
            st.write(f"**Comment:** {record['comment']}")
            st.write(f"**Summary:** {record['summary']}")
            st.write(f"**Sentiment:** {record['sentiment']}")
            st.write(f"**Status:** {record['status']}")

# ---------------------------
# Show user submissions
# ---------------------------
if st.session_state.user_id:
    st.markdown("---")
    st.subheader("📜 My Submissions")

    items = list_comments_for_user(st.session_state.user_id)
    if items:
        df = pd.DataFrame(items)
        st.dataframe(df[['sector',]()]()
