from crewai import Agent

from tools.cv_text_tool import CVTextTool


def create_cv_analyst(llm, cv_text: str) -> Agent:
    return Agent(
        role="Civil Engineering CV Analyst",
        goal=(
            "Extract the candidate's previous designations, years of "
            "experience if stated, civil engineering skills, project types, "
            "sectors, and software."
        ),
        backstory=(
            "You carefully analyze candidate-provided CV descriptions. "
            "Use the CV description reader tool. Do not guess missing dates, "
            "experience, qualifications, or skills. Do not repeat private "
            "contact information."
        ),
        tools=[CVTextTool(cv_text=cv_text)],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
