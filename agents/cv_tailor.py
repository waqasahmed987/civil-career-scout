from crewai import Agent


def create_cv_tailor(llm) -> Agent:
    return Agent(
        role="Evidence-Based CV Tailoring Assistant",
        goal=(
            "Create an editable CV draft for a job the user selected, using "
            "only facts in the user's pasted CV description."
        ),
        backstory=(
            "You may reorganize and clarify existing facts to highlight "
            "relevant experience. Never invent qualifications, achievements, "
            "projects, dates, employers, or skills. Put unsupported job "
            "criteria under GAPS TO REVIEW."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
