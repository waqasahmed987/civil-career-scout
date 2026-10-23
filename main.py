from io import BytesIO

import streamlit as st
from docx import Document
from pypdf import PdfReader

from crew_runner import find_jobs, tailor_cv


st.set_page_config(
    page_title="Civil Career Scout",
    page_icon="🏗️",
    layout="wide",
)


def extract_cv_text(uploaded_file) -> str:
    """Extract text from either a PDF or DOCX file held in memory."""
    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if file_name.endswith(".docx"):
        document = Document(BytesIO(file_bytes))
        parts = [paragraph.text for paragraph in document.paragraphs]

        # Also read text from tables, which are common in CV templates.
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))

        return "\n".join(parts)

    raise ValueError("Please upload a PDF or DOCX file.")


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
    .stApp {
      background: linear-gradient(135deg,#f4faf8,#f7f9fc 55%,#edf5fb);
    }
    .block-container {
      max-width: 1160px;
      padding-top: 2rem;
    }
    .hero {
      padding: 2.4rem;
      border-radius: 24px;
      color: white;
      background: linear-gradient(120deg,#10253c,#16445b 60%,#087d74);
      box-shadow: 0 18px 48px #15354c22;
    }
    .hero h1 {
      font-family: Manrope,sans-serif;
      font-size: 2.5rem;
      margin: .2rem 0;
    }
    .hero p {
      color: #d8e9ed;
      font-size: 1.05rem;
      margin: 0;
    }
    .eyebrow {
      color: #64e0c5;
      letter-spacing: .15em;
      font-size: .75rem;
      font-weight: 700;
    }
    div[data-testid="stFileUploader"] {
      border: 1px dashed #91cfc1;
      border-radius: 14px;
    }
    .stButton button {
      border-radius: 11px;
      font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">CIVIL ENGINEERING CAREER SEARCH</div>
      <h1>Find your next project.</h1>
      <p>Search jobs in Pakistan and the Middle East, review your matches,
      and prepare a CV draft for a job you select.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

with st.sidebar:
    st.header("Your search")

    api_key = st.text_input(
        "Groq API key",
        type="password",
        help="For a shared deployment, configure the key in Streamlit Secrets.",
    )

    locations = st.multiselect(
        "Target locations",
        [
            "Pakistan",
            "United Arab Emirates",
            "Saudi Arabia",
            "Qatar",
            "Oman",
            "Kuwait",
            "Bahrain",
        ],
        default=["Pakistan", "United Arab Emirates", "Saudi Arabia"],
    )

    max_jobs = st.slider("Maximum listings", 3, 8, 5)

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("1 · Upload your CV")
    cv_file = st.file_uploader(
        "Choose a PDF or DOCX CV",
        type=["pdf", "docx"],
        help=(
            "Text-based PDFs and DOCX are supported. Scanned image-only PDFs "
            "need OCR, which is not included."
        ),
    )

    if cv_file:
        st.success(f"Ready to search: {cv_file.name}")

with right:
    st.subheader("2 · You stay in control")
    st.markdown(
        """
        - Agents extract, search, compare, and draft.
        - You review the extracted profile and original job listings.
        - You choose if and when to apply.
        - The app never submits an application.
        """
    )

search_clicked = st.button(
    "Search matching jobs",
    type="primary",
    use_container_width=True,
    disabled=not cv_file or not locations,
)

if search_clicked:
    if not api_key:
        st.error("Enter your Groq API key in the sidebar.")
        st.stop()

    if len(cv_file.getvalue()) > 8 * 1024 * 1024:
        st.error("Please upload a file smaller than 8 MB.")
        st.stop()

    try:
        cv_text = extract_cv_text(cv_file)
    except Exception as exc:
        st.error(f"Could not read this CV: {exc}")
        st.stop()

    if not cv_text.strip():
        st.error(
            "No readable text was found. If this is a scanned PDF, "
            "use a text-based PDF or DOCX file."
        )
        st.stop()

    status = st.status("Starting your search…", expanded=True)
    progress = st.progress(0)

    stages = {
        "CV Analyst": 25,
        "Job Scout": 60,
        "Match Reviewer": 90,
    }

    def show_agent(agent_name: str, message: str):
        status.update(label=f"Now working: {agent_name}")
        status.write(f"🟢 **Now working: {agent_name}** — {message}")
        progress.progress(stages.get(agent_name, 0))

    try:
        profile, results = find_jobs(
            cv_text=cv_text,
            locations=locations,
            limit=max_jobs,
            api_key=api_key,
            on_stage=show_agent,
        )

        progress.progress(100)
        status.update(
            label="Search finished — review your results",
            state="complete",
            expanded=False,
        )

        st.session_state["cv_text"] = cv_text
        st.session_state["profile"] = profile
        st.session_state["results"] = results

    except Exception as exc:
        status.update(label="Search failed", state="error")
        st.error(f"Something went wrong: {exc}")

if "results" in st.session_state:
    results = st.session_state["results"]

    st.divider()
    st.header("Your job matches")

    with st.expander("Review the profile extracted from your CV", expanded=True):
        st.write(results.get("profile_summary", st.session_state["profile"]))
        st.caption("Check this summary for extraction mistakes.")

    jobs = results.get("jobs", [])

    if not jobs:
        st.warning(
            "No listings with usable source links were found. Try more "
            "locations or broader job keywords."
        )

    for index, job in enumerate(jobs):
        with st.container(border=True):
            st.subheader(job.get("title", "Job title not found"))
            st.write(
                f"**{job.get('company', 'Company not listed')}** · "
                f"{job.get('location', 'Location not listed')}"
            )
            st.metric("Approximate match", f"{job.get('match_score', '—')}%")
            st.write(job.get("why_match", "Review the original listing."))

            if job.get("requirements"):
                st.caption(f"Listing requirements: {job['requirements']}")

            url = job.get("url", "")
            if url.startswith(("https://", "http://")):
                st.link_button("Open original listing", url)

            if st.button(
                "Prepare a CV draft for this job",
                key=f"tailor_{index}",
            ):
                try:
                    with st.status(
                        "Now working: CV Tailoring Agent",
                        expanded=True,
                    ) as tailor_status:
                        tailor_status.write(
                            "🟢 **Now working: CV Tailoring Agent** — "
                            "preparing a draft from your existing CV facts."
                        )
                        draft = tailor_cv(
                            cv_text=st.session_state["cv_text"],
                            selected_job=job,
                            api_key=api_key,
                        )
                        tailor_status.update(
                            label="Draft ready for your review",
                            state="complete",
                            expanded=False,
                        )

                    st.session_state["cv_draft"] = draft
                    st.session_state["cv_draft_job"] = job.get(
                        "title",
                        "selected job",
                    )

                except Exception as exc:
                    st.error(f"Could not prepare a CV draft: {exc}")

    if results.get("notes"):
        st.info(results["notes"])

if "cv_draft" in st.session_state:
    st.divider()
    st.header("Edit and download your tailored CV")

    st.warning(
        "Review each line before using this draft. The agent can reorganize "
        "your experience, but should not add facts absent from your CV."
    )

    edited_cv = st.text_area(
        f"Draft for: {st.session_state.get('cv_draft_job', 'selected job')}",
        value=st.session_state["cv_draft"],
        height=520,
    )

    st.session_state["cv_draft"] = edited_cv

    doc = Document()
    doc.add_heading("CV", level=0)

    for line in edited_cv.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.isupper() and len(line) < 60:
            doc.add_heading(line.title(), level=1)
        else:
            doc.add_paragraph(line)

    output = BytesIO()
    doc.save(output)
    output.seek(0)

    st.download_button(
        "Download reviewed CV draft (.docx)",
        data=output.getvalue(),
        file_name="tailored_cv_draft.docx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        type="primary",
        use_container_width=True,
    )

st.divider()
st.caption(
    "AI-assisted job discovery. Search results can be stale. "
    "Verify listings at their original source. You make every decision."
)
