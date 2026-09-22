import os
import json
import time

from dotenv import load_dotenv
from google import genai


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")


client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# GEMINI MODELS
# =========================================================

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]


# =========================================================
# JSON CLEANING
# =========================================================

def _clean_json(text):
    """
    Clean Gemini response before JSON parsing.
    """

    text = (text or "").strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return text


# =========================================================
# NORMALIZE SKILL GAP DATA
# =========================================================

def _normalize_skill_gaps(skill_gaps):
    """
    Accept multiple skill-gap formats.

    Supported:

    1. Simple strings:

       [
           "AWS",
           "Spring Boot",
           "Docker"
       ]

    2. Interview skill-gap dictionaries:

       [
           {
               "skill": "Java",
               "average_score": 4.2,
               "level": "Developing",
               "missing_concepts": [],
               "strengths": []
           }
       ]

    3. Other dictionary formats containing:
       skill / score / average_score / priority / frequency
    """

    normalized = []

    if not isinstance(skill_gaps, list):
        return normalized

    for item in skill_gaps:

        # -------------------------------------------------
        # FORMAT 1: STRING
        # -------------------------------------------------

        if isinstance(item, str):

            skill = item.strip()

            if not skill:
                continue

            normalized.append({
                "skill": skill,
                "score": 0,
                "level": "Beginner",
                "missing_concepts": [],
                "strengths": [],
                "priority": "High"
            })

            continue

        # -------------------------------------------------
        # FORMAT 2: DICTIONARY
        # -------------------------------------------------

        if isinstance(item, dict):

            skill = (
                item.get("skill")
                or item.get("name")
                or item.get("technology")
                or item.get("title")
            )

            if not skill:
                continue

            score = item.get(
                "average_score",
                item.get(
                    "score",
                    0
                )
            )

            level = item.get(
                "level",
                "Beginner"
            )

            missing_concepts = item.get(
                "missing_concepts",
                []
            )

            strengths = item.get(
                "strengths",
                []
            )

            priority = item.get(
                "priority",
                "Medium"
            )

            frequency = item.get(
                "frequency",
                item.get(
                    "job_count",
                    0
                )
            )

            if not isinstance(
                missing_concepts,
                list
            ):
                missing_concepts = [
                    str(missing_concepts)
                ]

            if not isinstance(
                strengths,
                list
            ):
                strengths = [
                    str(strengths)
                ]

            normalized.append({
                "skill": str(skill),
                "score": score,
                "level": level,
                "missing_concepts": missing_concepts[:8],
                "strengths": strengths[:5],
                "priority": priority,
                "frequency": frequency
            })

    return normalized


# =========================================================
# DETERMINISTIC FALLBACK ROADMAP
# =========================================================

def _fallback_roadmap(
    role,
    skill_gaps
):
    """
    Creates a roadmap without Gemini.

    This guarantees that the application still works if
    Gemini is temporarily unavailable.
    """

    skills = []

    for item in skill_gaps:

        skill = item.get(
            "skill",
            "Unknown"
        )

        if skill and skill not in skills:
            skills.append(skill)

    # Limit to useful number of skills
    skills = skills[:12]

    if not skills:
        skills = [
            "Core technical fundamentals",
            "Problem solving",
            "SQL",
            "Git"
        ]

    # -----------------------------------------------------
    # Divide skills across four weeks
    # -----------------------------------------------------

    chunks = [
        skills[0:3],
        skills[3:6],
        skills[6:9],
        skills[9:12]
    ]

    # If fewer than four groups have content,
    # add role-relevant fundamentals.

    if not chunks[0]:
        chunks[0] = ["Core fundamentals"]

    if not chunks[1]:
        chunks[1] = ["Practical implementation"]

    if not chunks[2]:
        chunks[2] = ["Projects and integration"]

    if not chunks[3]:
        chunks[3] = ["Interview preparation"]


    weeks = []

    week_templates = [
        {
            "title": "Core Skill Foundations",
            "goal": "Build a strong foundation in the most important missing skills.",
            "why": "These fundamentals are required before moving into advanced role-specific work."
        },
        {
            "title": "Practical Development Skills",
            "goal": "Apply the missing technologies through small coding exercises.",
            "why": "Practical implementation helps convert theoretical knowledge into job-ready ability."
        },
        {
            "title": "Integration and Real-World Development",
            "goal": "Combine multiple skills into realistic development tasks.",
            "why": "Real projects require several technologies to work together."
        },
        {
            "title": "Project and Interview Preparation",
            "goal": "Consolidate the skills through projects and interview practice.",
            "why": "Interview preparation helps demonstrate the skills required for the target role."
        }
    ]


    for index in range(4):

        week_number = index + 1

        week_skills = chunks[index]

        topics = []

        for skill in week_skills:

            topics.append({
                "skill": skill,
                "concepts": [
                    f"{skill} fundamentals",
                    f"{skill} practical usage"
                ],
                "resource_query": (
                    f"{skill} tutorial "
                    f"for {role}"
                )
            })

        weeks.append({

            "week": week_number,

            "title":
                week_templates[index]["title"],

            "goal":
                week_templates[index]["goal"],

            "why_it_matters":
                week_templates[index]["why"],

            "topics":
                topics,

            "practice_task":
                (
                    f"Build a small {role} "
                    f"practice project using: "
                    f"{', '.join(week_skills)}."
                ),

            "completion_target":
                (
                    f"Complete at least 3 practical "
                    f"exercises covering "
                    f"{', '.join(week_skills)}."
                )
        })


    return {

        "role": role,

        "summary": (
            f"This 4-week roadmap is designed for "
            f"a {role} career path and focuses on "
            f"the skills identified as development gaps."
        ),

        "weeks": weeks,

        "total_weeks": 4
    }


# =========================================================
# GEMINI ROADMAP GENERATOR
# =========================================================

def generate_roadmap(
    role,
    skill_gaps
):
    """
    Generate a personalized learning roadmap.

    The function accepts BOTH:

    [
        "AWS",
        "Docker",
        "Spring Boot"
    ]

    and:

    [
        {
            "skill": "Java",
            "average_score": 4.5,
            "level": "Developing"
        }
    ]

    If Gemini fails, a deterministic fallback roadmap
    is returned instead of causing HTTP 500.
    """

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not role:
        role = "Software Developer"

    role = str(role).strip()

    normalized_gaps = _normalize_skill_gaps(
        skill_gaps
    )

    # -----------------------------------------------------
    # No skill gaps
    # -----------------------------------------------------

    if not normalized_gaps:

        return {

            "role": role,

            "summary": (
                "No specific skill gaps were provided. "
                "Focus on strengthening core technical "
                "skills and practical project experience."
            ),

            "weeks": [],

            "total_weeks": 0
        }


    # -----------------------------------------------------
    # Compact data for Gemini
    # -----------------------------------------------------

    compact_gaps = []

    for item in normalized_gaps[:15]:

        compact_gaps.append({

            "skill":
                item.get(
                    "skill",
                    "Unknown"
                ),

            "score":
                item.get(
                    "score",
                    0
                ),

            "level":
                item.get(
                    "level",
                    "Beginner"
                ),

            "priority":
                item.get(
                    "priority",
                    "Medium"
                ),

            "frequency":
                item.get(
                    "frequency",
                    0
                ),

            "missing_concepts":
                item.get(
                    "missing_concepts",
                    []
                )[:8],

            "strengths":
                item.get(
                    "strengths",
                    []
                )[:5]
        })


    # -----------------------------------------------------
    # Gemini prompt
    # -----------------------------------------------------

    prompt = f"""
You are an expert technical career mentor.

Create a personalized learning roadmap for:

Target role:
{role}

Candidate skill gaps:
{json.dumps(
    compact_gaps,
    ensure_ascii=False
)}

Requirements:

1. Create a practical 4-week roadmap.
2. Prioritize the most important missing skills.
3. Connect every week to the target role.
4. Each week must contain 2 to 4 topics.
5. Include practical coding or project work.
6. Include measurable completion targets.
7. Include learning resource SEARCH TOPICS only.
8. Do not invent URLs.
9. Focus on job-ready technical skills.
10. Make it realistic for 1 to 2 hours of study per day.
11. Avoid unrelated technologies.
12. Return ONLY valid JSON.
13. Do not use markdown.

Return exactly this structure:

{{
    "summary": "Short personalized summary",

    "weeks": [

        {{
            "week": 1,

            "title": "Week title",

            "goal": "Main learning goal",

            "why_it_matters":
                "Why this matters for the target role",

            "topics": [

                {{
                    "skill": "Skill name",

                    "concepts": [
                        "Concept 1",
                        "Concept 2"
                    ],

                    "resource_query":
                        "Search topic"
                }}

            ],

            "practice_task":
                "Practical coding/project task",

            "completion_target":
                "Measurable completion target"
        }}

    ]
}}
"""


    # -----------------------------------------------------
    # Try Gemini models
    # -----------------------------------------------------

    last_error = None

    for model in MODELS:

        try:

            print(
                f"Trying Gemini roadmap model: {model}"
            )

            response = client.models.generate_content(

                model=model,

                contents=prompt
            )

            content = _clean_json(
                response.text
            )

            roadmap_data = json.loads(
                content
            )

            if not isinstance(
                roadmap_data,
                dict
            ):
                raise ValueError(
                    "Gemini roadmap response "
                    "is not a JSON object."
                )


            weeks = roadmap_data.get(
                "weeks",
                []
            )

            if not isinstance(
                weeks,
                list
            ):
                raise ValueError(
                    "Gemini roadmap weeks "
                    "is not a list."
                )


            # -------------------------------------------------
            # Make sure roadmap contains useful weeks
            # -------------------------------------------------

            if len(weeks) == 0:

                raise ValueError(
                    "Gemini returned an empty roadmap."
                )


            roadmap_data["role"] = role

            roadmap_data["total_weeks"] = len(
                weeks
            )


            print(
                "Gemini roadmap generation "
                f"succeeded using {model}"
            )

            return roadmap_data


        except Exception as error:

            last_error = error

            print(
                f"Gemini roadmap model "
                f"{model} failed:"
            )

            print(
                repr(error)
            )

            error_text = str(error)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):
                time.sleep(2)

            else:
                time.sleep(1)


    # -----------------------------------------------------
    # ALL GEMINI MODELS FAILED
    # -----------------------------------------------------

    print(
        "All Gemini roadmap models failed."
    )

    print(
        "Using deterministic fallback roadmap."
    )

    return _fallback_roadmap(
        role,
        normalized_gaps
    )