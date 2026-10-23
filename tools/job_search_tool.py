from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field


class JobSearchInput(BaseModel):
    query: str = Field(
        description=(
            "Civil engineering designation, experience, skills, and target "
            "countries to search."
        ),
    )


class PublicJobSearchTool(BaseTool):
    name: str = "Public web and LinkedIn job search"
    description: str = (
        "Search public web results for civil engineering jobs. Searches both "
        "general job listings and publicly indexed LinkedIn job pages and "
        "company hiring posts. Does not access private or login-only LinkedIn "
        "content. Returns titles, links, and snippets for user verification."
    )
    args_schema: type[BaseModel] = JobSearchInput

    # CrewAI tool state; retained so the reviewer can only use found URLs.
    search_results: list[dict] = Field(default_factory=list, exclude=True)

    def _run(self, query: str) -> str:
        searches = [
            ("Web", query),
            ("LinkedIn jobs", f"site:linkedin.com/jobs/view {query}"),
            (
                "LinkedIn company posts",
                f"site:linkedin.com/posts hiring civil engineer {query}",
            ),
        ]

        output = []

        for source_name, search_query in searches:
            try:
                results = DDGS().text(search_query, max_results=5)

                for item in results:
                    url = item.get("href", "")
                    if not url.startswith(("https://", "http://")):
                        continue

                    result = {
                        "source_type": source_name,
                        "title": item.get("title", "")[:250],
                        "url": url,
                        "snippet": item.get("body", "")[:500],
                    }
                    self.search_results.append(result)
                    output.append(
                        f"SOURCE TYPE: {source_name}\n"
                        f"TITLE: {result['title']}\n"
                        f"URL: {url}\n"
                        f"SNIPPET: {result['snippet']}"
                    )
            except Exception as exc:
                output.append(f"{source_name} search failed: {exc}")

        if not output:
            return "No public results were returned. Try a broader query."

        # Keep tool output small enough for the model context.
        return "\n\n".join(output[:15])
