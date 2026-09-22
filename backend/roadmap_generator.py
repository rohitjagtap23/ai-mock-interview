import os
import json
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
]


def _clean_json(text):
    text = (text or "").strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return text


def generate_roadmap(role, skill_gaps):
    """
    Generate a practical, personalized learning roadmap.

    skill_gaps can contain:
      skill, average_score, level, missing_concepts, strengths, feedback
    """

    if not skill_gaps:
        return {
            "role": role,
            "summary": "No skill gaps were provided.",
            "weeks": [],
            "total_weeks": 0,
        }

    compact_gaps = []

    for item in skill_gaps[:10]:
        compact_gaps.append({
            "skill": item.get("skill", "Unknown"),
            "score": item.get("average_score", item.get("score", 0)),
            "level": item.get("level", "Beginner"),
            "missing_concepts": item.get("missing_concepts", [])[:8],
            "strengths": item.get("strengths", [])[:5],
        })

    prompt = f"""
You are an expert technical career mentor.

Create a personalized learning roadmap for this target role:
{role}

Candidate skill-gap data:
{json.dumps(compact_gaps, ensure_ascii=False)}

Create a practical roadmap that directly addresses the candidate's weakest skills.

Requirements:
1. Prioritize the weakest and most important skills first.
2. Connect the roadmap to the target role.
3. Create 4 to 6 weeks.
4. Each week must have a clear goal.
5. Each week must contain 2 to 4 skills/topics.
6. Include practical coding/project tasks.
7. Include a measurable completion target.
8. Include resources as search topics, not invented URLs.
9. Include a reason explaining why each week matters for the role.
10. Do not include unrelated topics.
11. Make the roadmap realistic for a learner studying about 1 to 2 hours per day.
12. Return ONLY valid JSON.
13. Do not use markdown.

Use exactly this structure:

{{
  "summary": "Short personalized summary",
  "weeks": [
    {{
      "week": 1,
      "title": "Week title",
      "goal": "Main learning goal",
      "why_it_matters": "Why this matters for the target role",
      "topics": [
        {{
          "skill": "Java",
          "concepts": ["Concept 1", "Concept 2"],
          "resource_query": "Java interview fundamentals"
        }}
      ],
      "practice_task": "Practical task",
      "completion_target": "Measurable target"
    }}
  ]
}}
"""

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

            roadmap_data = json.loads(content)

            if not isinstance(
                roadmap_data,
                dict
            ):
                raise ValueError(
                    "Roadmap response is not a JSON object."
                )

            weeks = roadmap_data.get(
                "weeks",
                []
            )

            if not isinstance(weeks, list):
                weeks = []

            roadmap_data["role"] = role
            roadmap_data["total_weeks"] = len(
                weeks
            )

            print(
                "Gemini roadmap generation succeeded "
                f"using {model}"
            )

            return roadmap_data

        except Exception as e:
            last_error = e

            print(
                f"Gemini roadmap model {model} failed:"
            )
            print(repr(e))

            error_text = str(e)

            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
            ):
                time.sleep(2)
            else:
                time.sleep(1)

    print(
        "All Gemini roadmap models failed."
    )

    raise last_error
