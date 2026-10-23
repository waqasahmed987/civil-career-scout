import json
import re

import crewai.llms.cache as crewai_cache
from crewai import Crew, LLM, Process, Task

from agents.cv_analyst import create_cv_analyst
from agents.cv_tailor import create_cv_tailor
from agents.job_scout import create_job_scout
from agents.match_reviewer import create_match_reviewer
from tools.job_search_tool import PublicJobSearchTool


# Workaround for CrewAI's Anthropic-specific cache marker with Groq.
crewai_cache.mark_cache_breakpoint = lambda message: message

MODEL_NAME = "openai/gpt-oss-120b"


def make_llm(api_key: str):
    return LLM(
        model=f"groq/{MODEL_NAME}",
        api_key=api_key,
        temperature=0.1,
    )


def run_agent(agent, description: str, expected_output: str) -> str:
    task = Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
    )
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )
    return str(crew.kickoff())


def extract_json(text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # If the reviewer didn't return valid JSON, the real search links
    # can still be displayed as unscored results.
    return {}


def find_jobs(cv_text: str, locations: list[str], limit: int, api_key: str, on_stage):
    cv_text = cv_text[:10000]
    llm = make_llm(api_key)

    on_stage("CV Analyst", "Reviewing your pasted CV description")
    profile = run_agent(
        create_cv_analyst(llm, cv_text),
        (
            "Use the CV description reader tool. Extract the candidate's "
            "previous job designations, experience duration if stated, "
            "technical skills, sectors, project types, and software. "
            "Do not include contact details. Keep the profile concise."
        ),
        "A concise factual candidate profile and relevant search keywords.",
    )
    profile = profile[:4000]

    on_stage("Job Scout", "Searching web and public LinkedIn results")
    search_tool = PublicJobSearchTool()
    scout = create_job_scout(llm, search_tool)

    search_evidence = run_agent(
        scout,
        (
            f"Candidate profile:\n{profile}\n\n"
            f"Target locations: {', '.join(locations)}.\n"
            "Use the Public web and LinkedIn job search tool. Search for "
            "civil engineering jobs matching the candidate's actual "
            "designations and stated experience. Include public web results, "
            "publicly indexed LinkedIn job pages, and public company hiring "
            "posts. Do not claim access to private or login-only content. "
            "Do not invent job details or URLs."
        ),
        "Concise public search evidence with original URLs.",
    )
    search_evidence = search_evidence[:2000]

    verified_source_results = search_tool.search_results[:15]
    evidence_json = json.dumps(
        verified_source_results,
        ensure_ascii=False,
    )[:9000]

    on_stage("Match Reviewer", "Comparing search evidence with your experience")
    reviewed = run_agent(
        create_match_reviewer(llm),
        (
            f"Candidate profile:\n{profile}\n\n"
            f"Original search evidence:\n{evidence_json}\n\n"
            f"Scout notes:\n{search_evidence}\n\n"
            "Return ONLY valid JSON with this structure:\n"
            "{"
            '"profile_summary": "string", '
            '"jobs": ['
            "{"
            '"title": "string", '
            '"company": "string", '
            '"location": "string", '
            '"url": "string", '
            '"source_type": "string", '
            '"match_score": 0, '
            '"why_match": "string", '
            '"requirements": "string"'
            "}"
            "], "
            '"notes": "string"'
            "}\n"
            f"Include at most {limit} jobs. Every URL must exactly match a "
            "URL in the original search evidence. Scores are approximate "
            "review aids, not probabilities or hiring decisions."
        ),
        "Valid JSON with cautious match explanations.",
    )

    data = extract_json(reviewed)

    allowed_by_url = {
        item["url"]: item
        for item in verified_source_results
        if item.get("url")
    }

    filtered_jobs = []

    for job in data.get("jobs", []):
        url = job.get("url", "")
        source = allowed_by_url.get(url)

        if source is None:
            continue

        job["source_type"] = source.get("source_type", "Web search")
        job["source_snippet"] = source.get("snippet", "")
        filtered_jobs.append(job)

    if not filtered_jobs:
        for source in verified_source_results[:limit]:
            filtered_jobs.append(
                {
                    "title": source.get("title") or "Open listing to review details",
                    "company": "See original listing",
                    "location": ", ".join(locations),
                    "url": source["url"],
                    "source_type": source.get("source_type", "Web search"),
                    "match_score": None,
                    "why_match": (
                        "Automatic match review was unavailable. "
                        "Compare this listing with your experience."
                    ),
                    "requirements": "",
                    "source_snippet": source.get("snippet", ""),
                }
            )

    data["jobs"] = filtered_jobs[:limit]

    if not data.get("profile_summary"):
        data["profile_summary"] = profile

    if not data.get("notes"):
        data["notes"] = (
            "Review each original listing and compare its requirements "
            "with your experience."
        )

    return profile, data


def tailor_cv(cv_text: str, selected_job: dict, api_key: str) -> str:
    llm = make_llm(api_key)
    agent = create_cv_tailor(llm)

    description = (
        "Create an editable plain-text CV draft for this job.\n\n"
        f"USER'S CV DESCRIPTION:\n{cv_text[:10000]}\n\n"
        "JOB SELECTED BY USER:\n"
        f"Designation: {selected_job.get('title', '')}\n"
        f"Company: {selected_job.get('company', '')}\n"
        f"Location: {selected_job.get('location', '')}\n"
        f"Requirements: {selected_job.get('requirements', '')}\n"
        f"Match explanation: {selected_job.get('why_match', '')}\n\n"
        "Use headings: PROFESSIONAL SUMMARY, TARGET DESIGNATIONS, KEY SKILLS, "
        "PROFESSIONAL EXPERIENCE, EDUCATION AND CERTIFICATIONS, GAPS TO REVIEW. "
        "Emphasize relevant designations and experience from the user's CV. "
        "Never invent facts. Return only the CV draft."
    )

    return run_agent(
        agent,
        description,
        "An editable CV draft based only on facts supplied by the user.",
    )
