# app.py
import streamlit as st
import io
import pandas as pd

# Safe import of Document
try:
    from docx import Document
except Exception:
    Document = None

# local modules (must exist in same repo)
from db import create_user, authenticate_user, add_comment, get_comment_by_passcode, list_comments_for_user
from nlp_backend import predict_sentiment, summarize_text, load_models

# ---------- Page config ----------
st.set_page_config(page_title="MCA E-Consultation Portal", layout="wide")

# ---------- Simple CSS ----------
st.markdown(
    """
    <style>
    .reportview-container { background: #f7fbff; }
    .stButton>button { background-color: #0b66c3; color: white; border-radius: 8px; }
    .stDownloadButton>button { background-color: #1a7f37; color: white; border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.image("https://upload.wikimedia.org/wikipedia/commons/4/4f/Emblem_of_India.svg", width=56)
st.title("🇮🇳 MCA — E-Consultation Portal")
st.caption("Smart India Hackathon 2025 — AI Sentiment & Summary (Demo)")

# ---------- Session defaults ----------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

# ---------- Sidebar: auth ----------
st.sidebar.header("User Access")
if st.session_state.user_id is None:
    auth_action = st.sidebar.radio("Choose", ["Login", "Register", "Guest"])
    if auth_action == "Register":
        reg_user = st.sidebar.text_input("Username", key="reg_user")
        reg_pass = st.sidebar.text_input("Password", type="password", key="reg_pass")
        reg_mobile = st.sidebar.text_input("Mobile (optional)", key="reg_mob")
        if st.sidebar.button("Create Account"):
            ok, msg = create_user(reg_user, reg_pass, reg_mobile)
            if ok:
                st.sidebar.success("Account created. Please login.")
            else:
                st.sidebar.error(f"Error: {msg}")
    elif auth_action == "Login":
        login_user = st.sidebar.text_input("Username", key="login_user")
        login_pass = st.sidebar.text_input("Password", type="password", key="login_pass")
        if st.sidebar.button("Login"):
            ok, val = authenticate_user(login_user, login_pass)
            if ok:
                st.session_state.user_id = val
                st.session_state.username = login_user
                st.sidebar.success("Logged in")
            else:
                st.sidebar.error(val)
    else:
        st.sidebar.info("Continue as Guest (limited features).")
else:
    st.sidebar.success(f"Signed in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.experimental_rerun()

# Option to load heavy NLP models
use_nlp = st.sidebar.checkbox("Enable full NLP models (may be slow)", value=False)
if use_nlp:
    with st.spinner("Loading NLP models..."):
        load_models()

# ---------- Main UI ----------
SECTORS = [
    "Agriculture", "Mining and quarrying", "Manufacturing", "Electricity and gas",
    "Construction", "Trade", "Transport", "Business service"
]

st.header("What would you like to do?")
col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Submit New Comment"):
        st.session_state.page = "submit"
with col2:
    if st.button("🔎 Track Complaint"):
        st.session_state.page = "track"

page = st.session_state.get("page", "home")

if page == "home":
    st.markdown(
        """
        **Quick steps:**  
        1. Login / Register (or continue as Guest).  
        2. Submit feedback under the correct sector. You will get an acknowledgement passcode.  
        3. Use passcode to track your complaint status.
        """
    )
    st.info("Enable full NLP models only if you want model-driven sentiment & summaries (may be slower).")

# ---------- Submit page ----------
if page == "submit":
    st.subheader("Submit New Comment")
    # If guest, ask name (not required for logged in users)
    if st.session_state.user_id is None:
        st.warning("You are submitting as Guest. For tracking, register or login to receive persistent submissions.")
        name = st.text_input("Name (for acknowledgement)", key="guest_name")
    sector = st.selectbox("Select sector", SECTORS)
    comment_text = st.text_area("Type your comment here", height=180, placeholder="Type complaint, feedback or suggestion...")

    if st.button("Submit"):
        if not comment_text or len(comment_text.strip()) < 5:
            st.error("Please enter a valid comment (min 5 characters).")
        else:
            sentiment, score = predict_sentiment(comment_text, use_model=use_nlp)
            summary = summarize_text(comment_text, use_model=use_nlp)
            user_id = st.session_state.user_id if st.session_state.user_id is not None else 0
            passcode = add_comment(user_id, sector, comment_text, sentiment, summary)
            st.success("✅ Comment submitted successfully.")
            st.info(f"Acknowledgement passcode: **{passcode}** — save this to track your complaint.")
            st.write(f"**Detected sentiment:** {sentiment}  |  **Summary:** {summary}")

# ---------- Track page ----------
if page == "track":
    st.subheader("Track Complaint")
    track_code = st.text_input("Enter acknowledgement passcode", key="track_code")
    if st.button("Track"):
        if not track_code or len(track_code.strip()) < 4:
            st.error("Enter a valid passcode.")
        else:
            rec = get_comment_by_passcode(track_code.strip())
            if not rec:
                st.error("Passcode not found.")
            else:
                st.success("Record found")
                st.write("**Sector:**", rec["sector"])
                st.write("**Comment:**", rec["comment"])
                st.write("**Summary:**", rec["summary"])
                st.write("**Sentiment:**", rec["sentiment"])
                st.write("**Status:**", rec["status"])

# ---------- My submissions + Report (visible for logged-in users) ----------
if st.session_state.user_id:
    st.markdown("---")
    st.subheader("📋 My Submissions")
    data = list_comments_for_user(st.session_state.user_id)  # list of dicts

    if data:
        df = pd.DataFrame(data)
        st.dataframe(df[["sector", "comment", "sentiment", "passcode"]], use_container_width=True)
    else:
        st.info("You have no submissions yet.")

    # Word report generation (only if python-docx available)
    st.subheader("📄 Generate Summary Word Report")
    if Document is None:
        st.error("`python-docx` is not installed on the environment. Add `python-docx` to requirements.txt and redeploy.")
    else:
        if st.button("Generate Word Report"):
            # ensure we re-fetch in case of concurrency
            data = list_comments_for_user(st.session_state.user_id)
            if not data:
                st.warning("No comments found to include in the report.")
            else:
                doc = Document()
                doc.add_heading("E-Consultation Summary Report", level=1)
                doc.add_paragraph(f"Generated for: {st.session_state.username}")
                doc.add_paragraph(f"Total Comments: {len(data)}")
                doc.add_paragraph("")

                for i, it in enumerate(data, start=1):
                    doc.add_heading(f"Comment #{i}", level=2)
                    doc.add_paragraph(f"Sector: {it.get('sector','')}")
                    doc.add_paragraph(f"Passcode: {it.get('passcode','')}")
                    doc.add_paragraph(f"Comment: {it.get('comment','')}")
                    doc.add_paragraph(f"Sentiment: {it.get('sentiment','')}")
                    doc.add_paragraph(f"Summary: { (it.get('comment','')[:140] + '...') if it.get('comment') else '' }")
                    doc.add_paragraph("")

                buf = io.BytesIO()
                doc.save(buf)
                buf.seek(0)

                st.download_button(
                    label="⬇️ Download Word Report (.docx)",
                    data=buf,
                    file_name="econsultation_summary.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

# ---------- Footer ----------
st.markdown("---")
st.caption("Demo app for Smart India Hackathon 2025 — E-Consultation Sentiment Analysis")
