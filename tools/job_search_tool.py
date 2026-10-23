from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field


class JobSearchInput(BaseModel):
    query: str = Field(
        description="Civil engineering job title, skill, and target location.",
    )


class PublicJobSearchTool(BaseTool):
    name: str = "Public web job search"
    description: str = (
        "Search public web results for job listings. Returns titles, URLs, "
        "and snippets. The user should verify each result at its source."
    )
    args_schema: type[BaseModel] = JobSearchInput

    def _run(self, query: str) -> str:
        try:
            results = DDGS().text(query, max_results=8)
            rows = []

            for result in results:
                url = result.get("href", "")
                if url.startswith(("https://", "http://")):
                    rows.append(
                        f"TITLE: {result.get('title', '')}\n"
                        f"URL: {url}\n"
                        f"SNIPPET: {result.get('body', '')}"
                    )

            return "\n\n".join(rows) if rows else "No public results found."
        except Exception as exc:
            return f"Public web search failed: {exc}"
