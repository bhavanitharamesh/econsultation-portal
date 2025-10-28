import streamlit as st
from db import create_user, authenticate_user, add_comment, get_comment_by_passcode, list_comments_for_user
from nlp_backend import predict_sentiment, summarize_text, load_models
import pandas as pd

st.set_page_config(page_title="MCA E-Consultation Portal", layout="wide")

# --- Simple CSS
st.markdown("""
<style>
.reportview-container { background: #f7fbff; }
.stButton>button { background-color: #0b66c3; color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.image("https://upload.wikimedia.org/wikipedia/commons/4/4f/Emblem_of_India.svg", width=60)
st.title("🇮🇳 Ministry of Corporate Affairs — E-Consultation Portal")
st.caption("Smart India Hackathon 2025 | AI-based Sentiment Analysis System")

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

# Sidebar Login/Register
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
                st.sidebar.success("Logged in")
            else:
                st.sidebar.error(val)
else:
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.experimental_rerun()

use_nlp = st.sidebar.checkbox("Enable full NLP models", value=False)
if use_nlp:
    load_models()

SECTORS = [
    "Agriculture", "Mining and quarrying", "Manufacturing", "Electricity and gas",
    "Construction", "Trade", "Transport", "Business service"
]

page = st.radio("Choose Action", ["Submit Comment", "Track Complaint"], horizontal=True)

if page == "Submit Comment":
    st.subheader("Submit New Comment")
    sector = st.selectbox("Select Sector", SECTORS)
    comment = st.text_area("Enter your comment", height=150)

    if st.button("Submit"):
        if not comment.strip():
            st.error("Please enter a comment")
        else:
            sentiment, score = predict_sentiment(comment, use_model=use_nlp)
            summary = summarize_text(comment, use_model=use_nlp)
            user_id = st.session_state.user_id if st.session_state.user_id else 0
            code = add_comment(user_id, sector, comment, sentiment, summary)
            st.success(f"✅ Submitted Successfully! Your Passcode: {code}")
            st.info(f"Sentiment: {sentiment.capitalize()} | Summary: {summary}")

elif page == "Track Complaint":
    st.subheader("Track your Complaint")
    code = st.text_input("Enter your Passcode")
    if st.button("Track"):
        rec = get_comment_by_passcode(code.strip())
        if not rec:
            st.error("No record found!")
        else:
            st.write(f"**Sector:** {rec['sector']}")
            st.write(f"**Comment:** {rec['comment']}")
            st.write(f"**Summary:** {rec['summary']}")
            st.write(f"**Sentiment:** {rec['sentiment']}")
            st.write(f"**Status:** {rec['status']}")

if st.session_state.user_id:
    st.markdown("---")
    st.subheader("My Submissions")
    for r in list_comments_for_user(st.session_state.user_id):
        st.write(f"📌 {r['sector']} | Passcode: `{r['passcode']}` | {r['sentiment']}")
        st.caption(r['comment'])
