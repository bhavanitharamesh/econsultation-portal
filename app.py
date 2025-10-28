import streamlit as st
from db import create_user, authenticate_user, add_comment, get_comment_by_passcode, list_comments_for_user
from nlp_backend import predict_sentiment, summarize_text, load_models
from docx import Document
import io
import pandas as pd

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="MCA E-Consultation Portal", layout="wide")

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
.reportview-container { background: #f7fbff; }
.stButton>button { background-color: #0b66c3; color: white; border-radius: 8px; }
.stDownloadButton>button { background-color: #1a7f37; color: white; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.image("https://upload.wikimedia.org/wikipedia/commons/4/4f/Emblem_of_India.svg", width=60)
st.title("🇮🇳 Ministry of Corporate Affairs — E-Consultation Portal")
st.caption("Smart India Hackathon 2025 | AI-based Sentiment Analysis System")

# ---------- SESSION ----------
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

# ---------- SIDEBAR ----------
st.sidebar.header("User Access")
if st.session_state.user_id is None:
    action = st.sidebar.radio("Select", ["Login", "Register", "Guest"])
    if action == "Register":
        u = st.sidebar.text_input("Username")
        p = st.sidebar.text_input("Password", type="password")
        m = st.sidebar.text_input("Mobile (optional)")
        if st.sidebar.button("Create Account"):
            ok, msg = create_user(u, p, m)
            if ok:
                st.sidebar.success(msg)
            else:
                st.sidebar.error(msg)
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
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.experimental_rerun()

use_nlp = st.sidebar.checkbox("Enable full NLP models (slow)", value=False)
if use_nlp:
    load_models()

# ---------- MAIN ----------
SECTORS = [
    "Agriculture", "Mining and quarrying", "Manufacturing", "Electricity and gas",
    "Construction", "Trade", "Transport", "Business service"
]

page = st.radio("Choose Action", ["Submit Comment", "Track Complaint"], horizontal=True)

# ---------- SUBMIT COMMENT ----------
if page == "Submit Comment":
    st.subheader("Submit New Comment")
    sector = st.selectbox("Select Sector", SECTORS)
    comment = st.text_area("Enter your comment", height=150)

    if st.button("Submit Comment"):
        if not comment.strip():
            st.error("Please enter a valid comment")
        else:
            sentiment, score = predict_sentiment(comment, use_model=use_nlp)
            summary = summarize_text(comment, use_model=use_nlp)
            user_id = st.session_state.user_id if st.session_state.user_id else 0
            code = add_comment(user_id, sector, comment, sentiment, summary)
            st.success(f"✅ Submitted successfully! Your Passcode: {code}")
            st.info(f"Sentiment: {sentiment.capitalize()} | Summary: {summary}")

# ---------- TRACK COMPLAINT ----------
elif page == "Track Complaint":
    st.subheader("Track your Complaint")
    code = st.text_input("Enter your Passcode")
    if st.button("Track Complaint"):
        rec = get_comment_by_passcode(code.strip())
        if not rec:
            st.error("No record found!")
        else:
            st.write(f"**Sector:** {rec['sector']}")
            st.write(f"**Comment:** {rec['comment']}")
            st.write(f"**Summary:** {rec['summary']}")
            st.write(f"**Sentiment:** {rec['sentiment']}")
            st.write(f"**Status:** {rec['status']}")

# ---------- MY SUBMISSIONS ----------
if st.session_state.user_id:
    st.markdown("---")
    st.subheader("📋 My Submissions")

    data = list_comments_for_user(st.session_state.user_id)
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df[["sector", "comment", "sentiment", "passcode"]])
    else:
        st.info("No submissions yet.")

    # ---------- WORD REPORT GENERATION ----------
    st.subheader("📄 Generate Summary Word Report")
    if st.button("Generate Word Report"):
        if not data:
            st.warning("No comments found to include in the report.")
        else:
            doc = Document()
            doc.add_heading("E-Consultation Summary Report", level=1)
            doc.add_paragraph(f"Generated for: {st.session_state.username}")
            doc.add_paragraph(f"Total Comments: {len(data)}")

            for i, it in enumerate(data, start=1):
                doc.add_heading(f"Comment #{i}", level=2)
                doc.add_paragraph(f"Sector: {it['sector']}")
                doc.add_paragraph(f"Passcode: {it['passcode']}")
                doc.add_paragraph(f"Comment: {it['comment']}")
                doc.add_paragraph(f"Sentiment: {it['sentiment']}")
                doc.add_paragraph(f"Summary: {it['comment'][:100]}...")

            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            st.download_button(
                label="⬇️ Download Word Report",
                data=buffer,
                file_name="econsultation_summary.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

st.markdown("---")
st.caption("Built for Smart India Hackathon 2025 | AI-enabled Sentiment & Feedback Analysis")
