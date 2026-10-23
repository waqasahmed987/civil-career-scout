from crewai import Agent

from tools.job_search_tool import PublicJobSearchTool


def create_job_scout(llm, search_tool: PublicJobSearchTool) -> Agent:
    return Agent(
        role="Pakistan and Middle East Civil Engineering Job Scout",
        goal=(
            "Search public web listings for civil engineering jobs that fit "
            "the candidate's experience and previous designations."
        ),
        backstory=(
            "You are a careful job researcher. Use the public web and "
            "LinkedIn job search tool. Search using the candidate's prior "
            "designations and skills, not only a generic civil engineer "
            "query. Do not invent jobs, companies, requirements, or URLs. "
            "LinkedIn results must be publicly indexed."
        ),
        tools=[search_tool],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
