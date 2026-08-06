#import transcript
# from pathlib import Path
# from transcript import get_transcript_from_video
# #import Generate_summary
# from Generate_summary import generate

# video_path = input("Enter the path to your video or audio file: ")

# trans = get_transcript_from_video(video_path)

# summary_text = generate(trans)
# print("\n--- MEETING SUMMARY ---\n")
# print(summary_text)
# # Changed the output file extension to .txt
# with open("meeting_summary.txt", "w", encoding="utf-8") as f:
#     f.write(summary_text)



import streamlit as st
import tempfile
import os
from pathlib import Path

from transcript import get_transcript_from_video
from Generate_summary import generate


# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI Meeting Notes Generator",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------------- Custom CSS ----------------
st.markdown("""
<style>
    .main {
        background-color: #0f1116;
    }
    .app-title {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
        background: linear-gradient(90deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .app-subtitle {
        text-align: center;
        color: #9ca3af;
        margin-bottom: 2rem;
        font-size: 1rem;
    }
    .section-card {
        background-color: #1a1d27;
        border: 1px solid #2d2f3b;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #a5b4fc;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
    }
    .section-body {
        color: #e5e7eb;
        font-size: 0.98rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }
    div.stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #6366f1, #ec4899);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 0;
        font-size: 1rem;
    }
    div.stButton > button:hover {
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- Header ----------------
st.markdown('<div class="app-title">📝 AI Meeting Notes Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Upload a meeting recording and get a clean, structured summary in seconds</div>', unsafe_allow_html=True)


# ---------------- Session State ----------------
if "summary_text" not in st.session_state:
    st.session_state.summary_text = None


# ---------------- File Upload ----------------
uploaded_file = st.file_uploader(
    "Upload your video or audio file",
    type=["mp4", "mp3", "wav", "m4a", "mov", "mkv"],
    help="Supported formats: mp4, mp3, wav, m4a, mov, mkv"
)

col1, col2 = st.columns([1, 1])
with col1:
    generate_clicked = st.button("✨ Generate Summary", disabled=uploaded_file is None)
with col2:
    if st.session_state.summary_text:
        st.download_button(
            "⬇️ Download Summary (.txt)",
            data=st.session_state.summary_text,
            file_name="meeting_summary.txt",
            mime="text/plain",
        )


# ---------------- Processing ----------------
if generate_clicked and uploaded_file is not None:
    # Save uploaded file to a temp path so get_transcript_from_video can read it
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    try:
        with st.spinner("Transcribing audio/video... this may take a while for longer files"):
            transcript_text = get_transcript_from_video(temp_path)

        if transcript_text.startswith("Failed to upload file") or transcript_text.startswith("File processing failed"):
            st.error(transcript_text)
        else:
            with st.spinner("Generating meeting summary..."):
                summary_text = generate(transcript_text)

            st.session_state.summary_text = summary_text
            st.success("Summary generated successfully!")
    finally:
        os.remove(temp_path)


# ---------------- Display Summary ----------------
if st.session_state.summary_text:
    st.markdown("### 📋 Meeting Summary")

    # Parse the plain-text sections produced by Generate_summary.generate()
    known_sections = ["Title", "Date", "Participants", "Key Points", "Action Items", "Decisions"]
    sections = {name: [] for name in known_sections}
    current_section = None

    for line in st.session_state.summary_text.splitlines():
        stripped = line.strip()
        matched = False
        for name in known_sections:
            if stripped.startswith(f"{name}:"):
                current_section = name
                content = stripped[len(name) + 1:].strip()
                if content:
                    sections[name].append(content)
                matched = True
                break
        if not matched and current_section and stripped:
            sections[current_section].append(stripped)

    icons = {
        "Title": "🏷️",
        "Date": "📅",
        "Participants": "👥",
        "Key Points": "💡",
        "Action Items": "✅",
        "Decisions": "📌",
    }

    for name in known_sections:
        content = " ".join(sections[name]).strip()
        if not content:
            content = "None"
        st.markdown(f"""
        <div class="section-card">
            <div class="section-title">{icons.get(name, "")} {name}</div>
            <div class="section-body">{content}</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("View raw summary text"):
        st.text(st.session_state.summary_text)


