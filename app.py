import streamlit as st
import os
import json
import uuid
import hashlib
import tempfile
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import bcrypt
import Audio_transcript as at
from Generate_summary import generate

load_dotenv()

APP_NAME = "ARMSG"
FULL_NAME = "AI Recorded Meeting Summary Generator"
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
MEETINGS_FILE = DATA_DIR / "meetings.json"

DATA_DIR.mkdir(exist_ok=True)
if not USERS_FILE.exists():
    USERS_FILE.write_text("[]", encoding="utf-8")
if not MEETINGS_FILE.exists():
    MEETINGS_FILE.write_text("[]", encoding="utf-8")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_json(path, data):
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def authenticate(email, password):
    users = load_json(USERS_FILE)
    for user in users:
        if user["email"].lower() == email.lower():
            try:
                if bcrypt.checkpw(password.encode("utf-8"),
                                  user["password_hash"].encode("utf-8")):
                    return user
            except ValueError:
                return None
    return None


def create_user(name, email, password):
    users = load_json(USERS_FILE)
    if any(u["email"].lower() == email.lower() for u in users):
        return False, "An account with this email already exists."
    user = {
        "id": f"user_{uuid.uuid4().hex[:10]}",
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "auth_provider": "email",
        "created_at": datetime.now().isoformat(timespec="seconds")
    }
    users.append(user)
    save_json(USERS_FILE, users)
    return True, user


def user_meetings():
    if not st.session_state.get("logged_in"):
        return []
    meetings = load_json(MEETINGS_FILE)
    return [m for m in meetings if m["user_id"] == st.session_state["user_id"]]


def save_meeting(summary):
    meetings = load_json(MEETINGS_FILE)
    meetings.append({
        "meeting_id": f"meeting_{uuid.uuid4().hex[:10]}",
        "user_id": st.session_state["user_id"],
        "meeting_title": extract_title(summary),
        "date": datetime.now().strftime("%d %B %Y"),
        "summary": summary,
        "created_at": datetime.now().isoformat(timespec="seconds")
    })
    save_json(MEETINGS_FILE, meetings)


def extract_title(summary):
    for line in summary.splitlines():
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip() or "Untitled Meeting"
    return "Untitled Meeting"


def inject_css():
    st.markdown("""
    <style>
    #MainMenu, footer {visibility:hidden;}
    header {background:transparent !important;}
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 20% 0%, #202044 0%, #0b0c14 38%, #08090f 100%);
        color:#f5f7ff;
    }
    [data-testid="stSidebar"] {
        background:rgba(14,16,28,.94);
        border-right:1px solid rgba(255,255,255,.08);
    }
    .brand {font-size:25px;font-weight:800;letter-spacing:-1px;margin-bottom:2px;}
    .top-brand {font-size:22px;padding-top:5px;color:#f5f7ff;}
    [data-testid="stHorizontalBlock"] button {
        border-radius:10px;
    }
    .brand-sub {color:#9da5bd;font-size:12px;margin-bottom:25px;}
    .hero {text-align:center;padding:58px 15px 30px;}
    .hero h1 {font-size:48px;letter-spacing:-2px;margin-bottom:10px;}
    .hero p {font-size:17px;color:#aeb6ca;max-width:650px;margin:auto;}
    .pill {display:inline-block;padding:7px 13px;border-radius:30px;
           background:rgba(126,92,255,.14);color:#bdaeff;font-size:12px;
           border:1px solid rgba(126,92,255,.25);margin-bottom:16px;}
    .card {padding:28px;border-radius:20px;background:rgba(255,255,255,.045);
           border:1px solid rgba(255,255,255,.09);height:100%;
           box-shadow:0 15px 45px rgba(0,0,0,.18);}
    .card h3 {margin-top:0;}
    .muted {color:#9da5bd;}
    .notes {background:rgba(255,255,255,.045);color:#eef1fa;border-radius:18px;padding:34px;
            border:1px solid rgba(255,255,255,.10);
            box-shadow:0 20px 55px rgba(0,0,0,.24);line-height:1.75;
            white-space:pre-wrap;font-family:Inter,Arial,sans-serif;}
    .section-title {font-size:13px;font-weight:800;letter-spacing:1px;color:#7c5cff;
                    text-transform:uppercase;margin-top:24px;}
    .status {padding:12px 16px;border-radius:12px;background:rgba(126,92,255,.12);
             border:1px solid rgba(126,92,255,.25);}
    @media(max-width:800px){.hero h1{font-size:36px;}.card{margin-bottom:15px;}}
    </style>
    """, unsafe_allow_html=True)


def init_state():
    defaults = {
        "logged_in": False, "user_id": None, "user_name": None,
        "user_email": None, "page": "home", "summary": None,
        "input_mode": "Recorded Meeting", "selected_meeting": None, "transcript": None
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">🎙️ ARMSG</div><div class="brand-sub">AI Meeting Summary</div>',
                    unsafe_allow_html=True)

        if st.button("＋ New Meeting", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.summary = None
            st.session_state.transcript = None
            st.session_state.selected_meeting = None
            st.rerun()

        st.markdown("---")
        st.markdown("### History")

        if st.session_state.logged_in:
            meetings = user_meetings()
            if not meetings:
                st.caption("No saved meetings yet.")
            for m in reversed(meetings):
                if st.button(f"📄 {m['meeting_title'][:27]}", key=m["meeting_id"],
                             use_container_width=True):
                    st.session_state.selected_meeting = m
                    st.session_state.page = "history"
                    st.rerun()
        else:
            st.caption("No saved history.")
            st.info("🔐 Sign up to see your history.")

        st.markdown("---")
        if st.session_state.logged_in:
            st.markdown(f"👤 **{st.session_state.user_name}**")
            st.caption(st.session_state.user_email)
            if st.button("Logout", key="sidebar_logout", use_container_width=True):
                logout_user()
        else:
            st.markdown("**Guest Mode**")
            st.caption("Use ARMSG first. Sign up only when you want history.")


def logout_user():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.page = "home"
    st.session_state.summary = None
    st.session_state.selected_meeting = None
    st.rerun()


def top_navigation():
    # Real Streamlit buttons: these are functional controls, not decorative HTML.
    left, spacer, login_col, signup_col = st.columns([5.5, 1.5, 1.4, 1.4])
    with left:
        st.markdown('<div class="top-brand">🎙️ <b>ARMSG</b></div>', unsafe_allow_html=True)

    if st.session_state.logged_in:
        with login_col:
            if st.button("👤 Profile", key="top_profile", use_container_width=True):
                st.session_state.page = "history"
                st.rerun()
        with signup_col:
            if st.button("Logout", key="top_logout", use_container_width=True):
                logout_user()
    else:
        with login_col:
            if st.button("Sign In", key="top_signin", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
        with signup_col:
            if st.button("Sign Up", key="top_signup", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()


def auth_page(kind):
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown('<div class="pill">ARMSG • AI MEETING NOTES</div>', unsafe_allow_html=True)
    st.markdown(f"<h1>{'Welcome Back 👋' if kind == 'login' else 'Create Your ARMSG Account 🚀'}</h1>",
                unsafe_allow_html=True)
    st.markdown(f"<p>{'Sign in to access your history.' if kind == 'login' else 'Save and access your meeting history.'}</p></div>",
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if kind == "login":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True, type="primary"):
                user = authenticate(email.strip(), password)
                if user:
                    st.session_state.update(logged_in=True, user_id=user["id"],
                                            user_name=user["name"], user_email=user["email"],
                                            page="home")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")
            st.markdown("---")
            st.info("Google OAuth can be connected through the project's .env configuration.")
            if st.button("Create an account", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
            if st.button("← Continue as Guest", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
        else:
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            if st.button("Create Account", use_container_width=True, type="primary"):
                if not all([name.strip(), email.strip(), password, confirm]):
                    st.warning("⚠️ Please fill in all fields.")
                elif password != confirm:
                    st.error("❌ Passwords do not match.")
                elif len(password) < 6:
                    st.warning("⚠️ Password should contain at least 6 characters.")
                else:
                    ok, result = create_user(name.strip(), email.strip(), password)
                    if ok:
                        st.success("✨ Account created. You can now sign in.")
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
            st.markdown("---")
            st.info("Google OAuth can be connected through the project's .env configuration.")
            if st.button("Sign In", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
            if st.button("← Continue as Guest", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()


def home():
    st.markdown("""
    <div class="hero">
      <div class="pill">✨ AI-POWERED MEETING NOTES</div>
      <h1>Welcome to ARMSG 👋</h1>
      <p>Turn your meetings into clear, structured and actionable notes with AI.</p>
    </div>
    """, unsafe_allow_html=True)

    a, b = st.columns(2)
    with a:
        st.markdown("""
        <div class="card">
        <h3>🎙️ Recorded Meeting</h3>
        <p class="muted">Upload an audio or video recording and let your existing transcription backend do the work.</p>
        </div>
        """, unsafe_allow_html=True)
    with b:
        st.markdown("""
        <div class="card">
        <h3>📝 Meeting Transcript</h3>
        <p class="muted">Already have a transcript? Paste it directly and send it to the existing summarization backend.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("###")
    mode = st.radio("Input method", ["Recorded Meeting", "Meeting Transcript"],
                    horizontal=True, label_visibility="collapsed")
    st.session_state.input_mode = mode

    if mode == "Recorded Meeting":
        uploaded = st.file_uploader(
            "🎙️ Upload your meeting recording",
            type=["mp3", "wav", "m4a", "ogg", "webm", "mp4", "mov", "mkv"],
            help="Supported audio/video files"
        )
        if uploaded:
            st.success(f"Selected: **{uploaded.name}**")
            if st.button("✨ Generate Meeting Notes", type="primary", use_container_width=True):
                suffix = Path(uploaded.name).suffix.lower()
                temp_path = None
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded.getbuffer())
                        temp_path = tmp.name

                    with st.status("🎙️ Processing recording...", expanded=True) as status:
                        st.write("📤 Uploading audio/video for transcription...")

                        # The original transcription backend is preserved.
                        # Gemini can temporarily return HTTP 503 when its model
                        # is overloaded, so retry the existing function itself.
                        max_attempts = 3
                        transcript = None
                        last_error = None

                        for attempt in range(1, max_attempts + 1):
                            try:
                                if attempt > 1:
                                    wait_seconds = 10 * (2 ** (attempt - 2))
                                    st.write(
                                        f"🔄 Gemini is temporarily busy. "
                                        f"Retrying in {wait_seconds} seconds "
                                        f"(attempt {attempt}/{max_attempts})..."
                                    )
                                    time.sleep(wait_seconds)

                                transcript = at.get_transcript_from_video(temp_path)

                                if transcript and transcript.strip() and not (
                                    transcript.startswith("Failed to upload file:")
                                    or transcript.startswith("File processing failed")
                                ):
                                    break

                                last_error = transcript or "Empty transcript returned."

                            except Exception as exc:
                                last_error = str(exc)
                                error_text = str(exc).lower()
                                transient = (
                                    "503" in error_text
                                    or "unavailable" in error_text
                                    or "high demand" in error_text
                                    or "service unavailable" in error_text
                                )

                                if not transient or attempt == max_attempts:
                                    raise

                        if not transcript or not transcript.strip():
                            raise RuntimeError(
                                last_error or
                                "The transcription backend returned an empty transcript."
                            )

                        if transcript.startswith("Failed to upload file:") or transcript.startswith("File processing failed"):
                            raise RuntimeError(transcript)

                        st.write("✅ Transcript generated successfully.")
                        st.write(f"📝 Transcript length: {len(transcript.split())} words")
                        st.write("🤖 Sending transcript to the existing AI summarizer...")

                        # IMPORTANT: this is the existing backend function.
                        summary = generate(transcript)
                        if not summary or not summary.strip():
                            raise RuntimeError("The summarization backend returned an empty summary.")

                        st.session_state.summary = summary
                        st.session_state.transcript = transcript
                        if st.session_state.logged_in:
                            save_meeting(summary)
                        status.update(label="✅ Meeting notes generated successfully!", state="complete")
                except Exception as e:
                    error_text = str(e)
                    if (
                        "503" in error_text
                        or "high demand" in error_text.lower()
                        or "unavailable" in error_text.lower()
                    ):
                        st.error("⚠️ Gemini is temporarily overloaded (HTTP 503).")
                        st.info(
                            "ARMSG retried the transcription automatically. "
                            "Please wait a little and try again if Gemini is still unavailable."
                        )
                    else:
                        st.error("❌ We couldn't complete the audio/video processing.")
                        st.warning("The failure occurred during transcription or summarization.")
                    st.code(error_text)
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except OSError:
                            pass

            if st.session_state.get("transcript"):
                with st.expander("📝 View Generated Transcript"):
                    st.text_area("Transcript", st.session_state.transcript, height=300, label_visibility="collapsed")

    else:
        transcript = st.text_area("📝 Paste your meeting transcript",
                                  height=300,
                                  placeholder="Paste transcript here...")
        txt_file = st.file_uploader("OR upload a .txt transcript", type=["txt"])
        if txt_file:
            transcript = txt_file.read().decode("utf-8", errors="ignore")
            st.text_area("Transcript preview", transcript, height=180)
        if st.button("✨ Generate Meeting Notes", type="primary", use_container_width=True):
            if not transcript.strip():
                st.warning("⚠️ Please enter a meeting transcript.")
            else:
                try:
                    with st.status("Generating meeting notes...", expanded=False):
                        summary = generate(transcript)
                    st.session_state.transcript = transcript
                    st.session_state.summary = summary
                    if st.session_state.logged_in:
                        save_meeting(summary)
                    st.success("✨ Meeting notes generated successfully!")
                except Exception as e:
                    st.error("❌ AI summarization failed. Please check your Groq API key.")
                    st.caption(str(e))

    if st.session_state.summary:
        display_summary(st.session_state.summary)


def display_summary(summary):
    st.markdown("## 📋 Meeting Notes")
    st.markdown(f'<div class="notes">{summary.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</div>',
                unsafe_allow_html=True)
    st.download_button(
        "⬇ Download Meeting Notes",
        data=summary,
        file_name="meeting_summary.txt",
        mime="text/plain",
        use_container_width=True
    )
    if not st.session_state.logged_in:
        st.info("✨ Want to save this meeting and access it later? Sign up for ARMSG history.")


def history_page():
    m = st.session_state.selected_meeting
    if not m:
        st.session_state.page = "home"
        st.rerun()
    st.markdown(f"## 📄 {m['meeting_title']}")
    st.caption(f"Date: {m['date']}")
    display_summary(m["summary"])
    if st.button("🗑️ Delete this meeting"):
        meetings = load_json(MEETINGS_FILE)
        meetings = [x for x in meetings if x["meeting_id"] != m["meeting_id"] or
                    x["user_id"] != st.session_state["user_id"]]
        save_json(MEETINGS_FILE, meetings)
        st.session_state.selected_meeting = None
        st.session_state.page = "home"
        st.success("Meeting deleted.")
        st.rerun()


st.set_page_config(page_title="ARMSG — AI Meeting Summary", page_icon="🎙️", layout="wide")
load_dotenv()
init_state()
inject_css()
sidebar()
top_navigation()

if st.session_state.page == "login":
    auth_page("login")
elif st.session_state.page == "signup":
    auth_page("signup")
elif st.session_state.page == "history":
    history_page()
else:
    home()
