import json
import re

import crewai.llms.cache as crewai_cache
from crewai import Crew, LLM, Process, Task

from agents.cv_analyst import create_cv_analyst
from agents.cv_tailor import create_cv_tailor
from agents.job_scout import create_job_scout
from agents.match_reviewer import create_match_reviewer


# Groq rejects CrewAI's Anthropic-specific cache marker.
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
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("The agent did not return the expected JSON. Please retry.")
    return json.loads(match.group(0))


def find_jobs(cv_text: str, locations: list[str], limit: int, api_key: str, on_stage):
    # Keep prompts smaller to reduce Groq tokens per request.
    cv_text = cv_text[:8000]
    llm = make_llm(api_key)

    on_stage("CV Analyst", "Reading your CV")
    profile = run_agent(
        create_cv_analyst(llm, cv_text),
        (
            "Use the CV text reader tool to review the supplied CV. Summarize "
            "stated civil engineering roles, experience duration if supported "
            "by dates, technical skills, project types, sectors, and software. "
            "Do not include contact details. Keep the profile under 150 words."
        ),
        "A concise evidence-based CV profile and job search keywords.",
    )

    on_stage("Job Scout", "Searching public job listings")
    search_results = run_agent(
        create_job_scout(llm),
        (
            f"Candidate CV profile:\n{profile[:4000]}\n\n"
            f"Search locations: {', '.join(locations)}.\n"
            f"Use the Public web job search tool. Find up to {limit} relevant "
            "civil engineering listings. Keep each title, employer if shown, "
            "location, original URL, and a short snippet. Do not invent details."
        ),
        "A short list of public job listings with original URLs.",
    )
    search_results = search_results[:6000]

    on_stage("Match Reviewer", "Reviewing match evidence")
    reviewed = run_agent(
        create_match_reviewer(llm),
        (
            f"CV profile:\n{profile[:4000]}\n\n"
            f"Public job search results:\n{search_results}\n\n"
            "Return ONLY valid JSON with this structure:\n"
            "{"
            '"profile_summary": "string", '
            '"jobs": ['
            "{"
            '"title": "string", '
            '"company": "string", '
            '"location": "string", '
            '"url": "string", '
            '"match_score": 0, '
            '"why_match": "string", '
            '"requirements": "string"'
            "}"
            "], "
            '"notes": "string"'
            "}\n"
            f"Include up to {limit} listings and only URLs starting with "
            "http or https. Scores are approximate review aids, not "
            "probabilities or hiring decisions. Explain each match briefly."
        ),
        "Valid JSON with a profile summary and cautious job matches.",
    )

    data = extract_json(reviewed)
    data["jobs"] = [
        job
        for job in data.get("jobs", [])
        if str(job.get("url", "")).startswith(("https://", "http://"))
    ]
    return profile, data


def tailor_cv(cv_text: str, selected_job: dict, api_key: str) -> str:
    llm = make_llm(api_key)
    agent = create_cv_tailor(llm)

    return run_agent(
        agent,
        (
            "Create an editable plain-text CV draft for the selected job.\n\n"
            f"ORIGINAL CV TEXT:\n{cv_text[:8000]}\n\n"
            "SELECTED JOB:\n"
            f"Title: {selected_job.get('title', '')}\n"
            f"Company: {selected_job.get('company', '')}\n"
            f"Location: {selected_job.get('location', '')}\n"
            f"Requirements: {selected_job.get('requirements', '')}\n"
            f"Match evidence: {selected_job.get('why_match', '')}\n\n"
            "Use headings: PROFESSIONAL SUMMARY, KEY SKILLS, PROFESSIONAL "
            "EXPERIENCE, EDUCATION AND CERTIFICATIONS, GAPS TO REVIEW. "
            "Reorganize existing facts to highlight relevant experience. "
            "Never invent qualifications, dates, skills, or achievements. "
            "Return only the CV draft."
        ),
        "An editable CV draft based only on the original CV facts.",
    )
