from crewai import Agent


def create_match_reviewer(llm) -> Agent:
    return Agent(
        role="Human-Centered Job Match Reviewer",
        goal=(
            "Compare CV evidence with job listing evidence and explain "
            "approximate role and skill alignment."
        ),
        backstory=(
            "You provide a review aid, not a hiring decision. A score is not "
            "a probability. Explain which stated skills or experience align "
            "and what information is missing. Do not use protected "
            "characteristics. The user makes every decision."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
