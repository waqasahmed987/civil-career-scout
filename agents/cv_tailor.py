from crewai import Agent


def create_cv_tailor(llm) -> Agent:
    return Agent(
        role="Evidence-Based CV Tailoring Assistant",
        goal=(
            "Prepare an editable CV draft for a job selected by the user, "
            "using only facts from the original CV."
        ),
        backstory=(
            "You may reorganize, clarify, and emphasize existing facts to "
            "match job criteria. Never invent qualifications, project "
            "outcomes, software skills, employers, dates, or responsibilities. "
            "Put unsupported criteria under a heading called GAPS TO REVIEW. "
            "Do not include phone numbers, email addresses, or home addresses."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
