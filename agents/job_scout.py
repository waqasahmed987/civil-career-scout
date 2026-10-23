from crewai import Agent

from tools.job_search_tool import PublicJobSearchTool


def create_job_scout(llm) -> Agent:
    return Agent(
        role="Pakistan and Middle East Civil Engineering Job Scout",
        goal=(
            "Find public web listings for civil engineering jobs in the "
            "locations selected by the user."
        ),
        backstory=(
            "You are a job researcher. Use the Public web job search tool. "
            "Keep original source URLs and result snippets. Never invent jobs, "
            "companies, requirements, or application links."
        ),
        tools=[PublicJobSearchTool()],
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )
