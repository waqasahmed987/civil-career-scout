import streamlit as st
from docx import Document
from io import BytesIO

from crew_runner import find_jobs, tailor_cv


st.set_page_config(
    page_title="Civil Career Scout",
    page_icon="🏗️",
    layout="wide",
)

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
      <p>Describe your experience, search relevant jobs, and prepare a CV
      draft for a role you select.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

with st.sidebar:
    st.header("Search settings")

    api_key = st.text_input(
        "Groq API key",
        type="password",
        help="Never add your API key to a GitHub file.",
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

    max_jobs = st.slider("Maximum jobs to show", 3, 8, 5)

st.subheader("Paste your CV description")

cv_text = st.text_area(
    "Include your previous designations, dates, experience, projects, "
    "responsibilities, skills, software, education, and certifications.",
    height=280,
    max_chars=10000,
    placeholder=(
        "Example:\n"
        "Senior Civil Engineer, 2019–2024 — managed site supervision for "
        "commercial and residential projects...\n"
        "Civil Site Engineer, 2015–2019 — reviewed drawings, coordinated "
        "subcontractors, and monitored concrete works...\n"
        "Skills: AutoCAD, Primavera P6, BOQ, quantity surveying..."
    ),
)

st.caption(
    "Avoid pasting your phone number, home address, passport number, or "
    "other sensitive personal information."
)

st.info(
    "Search includes general public web results and publicly indexed "
    "LinkedIn jobs and company posts. Private or login-only LinkedIn "
    "content is not available to this app."
)

search_clicked = st.button(
    "Search relevant jobs",
    type="primary",
    use_container_width=True,
    disabled=not cv_text.strip() or not locations,
)

if search_clicked:
    if not api_key:
        st.error("Enter your Groq API key in the sidebar.")
        st.stop()

    status = st.status("Starting your search…", expanded=True)
    progress = st.progress(0)

    stage_progress = {
        "CV Analyst": 25,
        "Job Scout": 60,
        "Match Reviewer": 90,
    }

    def update_agent(agent_name: str, message: str):
        status.update(label=f"Now working: {agent_name}")
        status.write(f"🟢 **Now working: {agent_name}** — {message}")
        progress.progress(stage_progress.get(agent_name, 0))

    try:
        profile, results = find_jobs(
            cv_text=cv_text,
            locations=locations,
            limit=max_jobs,
            api_key=api_key,
            on_stage=update_agent,
        )

        progress.progress(100)
        status.update(
            label="Search complete — review the results",
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

    with st.expander("Review the experience profile", expanded=True):
        st.write(results.get("profile_summary", st.session_state["profile"]))
        st.caption("Correct any mistakes in your pasted CV description and search again.")

    jobs = results.get("jobs", [])

    if not jobs:
        st.warning(
            "No verifiable listings were found. Try adding locations or "
            "including more detail about previous designations and skills."
        )



        
        for index, job in enumerate(jobs):
        with st.container(border=True):
            st.subheader(job.get("title", "Job title not listed"))
            st.write(
                f"**{job.get('company', 'Company not listed')}** · "
                f"{job.get('location', 'Location not listed')}"
            )
            st.caption(
                f"Source type: {job.get('source_type', 'Web search')}"
            )

            score = job.get("match_score")
            score_display = (
                f"{score}%"
                if isinstance(score, (int, float))
                else "Not scored"
            )
            st.metric("Approximate experience match", score_display)

            st.write(job.get("why_match", "Review the original listing."))

            if job.get("requirements"):
                st.caption(f"Requirements: {job['requirements']}")

            if job.get("source_snippet"):
                with st.expander("Search result snippet"):
                    st.write(job["source_snippet"])

            url = job.get("url", "")
            if url.startswith(("https://", "http://")):
                st.link_button("Open original job listing", url)

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
                            "preparing a draft from your pasted experience."
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
                    st.error(f"Could not prepare the CV draft: {exc}")

    if results.get("notes"):
        st.info(results["notes"])

if "cv_draft" in st.session_state:
    st.divider()
    st.header("Review and edit your CV draft")

    st.warning(
        "Review every detail before using this CV. The tailoring agent "
        "should only rearrange or clarify facts you provided."
    )

    edited_cv = st.text_area(
        f"Draft for: {st.session_state.get('cv_draft_job', 'selected job')}",
        value=st.session_state["cv_draft"],
        height=500,
        key="edited_cv_text",
    )

    document = Document()
    document.add_heading("CV", level=0)

    for line in edited_cv.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.isupper() and len(line) < 60:
            document.add_heading(line.title(), level=1)
        else:
            document.add_paragraph(line)

    output = BytesIO()
    document.save(output)
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
    "AI-assisted job discovery. Search results can be incomplete or outdated. "
    "Verify listings at their original source. You make every decision."
)
