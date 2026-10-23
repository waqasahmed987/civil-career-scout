from crewai import Agent

from tools.cv_text_tool import CVTextTool


def create_cv_analyst(llm, cv_text: str) -> Agent:
    return Agent(
        role="Civil Engineering CV Analyst",
        goal=(
            "Extract the candidate's stated civil engineering experience, "
            "skills, project types, sectors, and software."
        ),
        backstory=(
            "You are careful and factual. Use the CV text reader tool. "
            "Never guess missing dates, skills, qualifications, or experience. "
            "Do not repeat contact details such as phone, email, or address."
        ),
        tools=[CVTextTool(cv_text=cv_text)],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
