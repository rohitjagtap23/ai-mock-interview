import os
import re
import json
from datetime import datetime

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv

import serpapi
from supabase import create_client

from database import supabase
from skill_extractor import analyze_jobs, get_top_skills
from question_generator import generate_questions
from answer_evaluator import evaluate_answer
from skill_gap import calculate_skill_gaps
from roadmap_generator import generate_roadmap


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY")

if not SERPAPI_KEY:
    raise ValueError("SERPAPI_KEY is missing from .env")


# =========================================================
# CLIENTS
# =========================================================

serpapi_client = serpapi.Client(
    api_key=SERPAPI_KEY
)

# Separate Supabase client for validating frontend user access tokens.
# The database client in database.py continues to use SUPABASE_SECRET_KEY.
auth_supabase = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        auth_supabase = create_client(
            SUPABASE_URL,
            SUPABASE_ANON_KEY
        )
    except Exception as e:
        print("Auth client warning:", e)


def get_access_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise ValueError("Authorization token required")
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise ValueError("Authorization token is empty")
    return token


def get_authenticated_supabase():
    """Create a per-request Supabase client authenticated as the logged-in user."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_ANON_KEY is missing")

    token = get_access_token()
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(token)
    return client, token


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# HELPERS
# =========================================================

def require_user():
    try:
        client, token = get_authenticated_supabase()
        response = client.auth.get_user(token)
    except Exception as e:
        print("SUPABASE AUTH ERROR:", repr(e))
        raise ValueError(f"Supabase authentication failed: {e}") from e

    if not response or not response.user:
        raise ValueError("Invalid user")

    g.user_supabase = client
    return response.user


def normalize_skill(skill):

    aliases = {

        "spring": "Spring Boot",

        "springboot": "Spring Boot",

        "rest": "REST APIs",

        "rest api": "REST APIs",

        "reactjs": "React",

        "javascript": "JavaScript",

        "postgres": "PostgreSQL"

    }

    key = skill.strip().lower()

    return aliases.get(
        key,
        skill.strip()
    )


def extract_resume_skills(text):

    if not text:
        return []

    text_lower = text.lower()

    skills = [

        "Java",
        "Spring Boot",
        "Spring",
        "Spring Security",
        "Microservices",
        "REST APIs",
        "REST",
        "SQL",
        "MySQL",
        "PostgreSQL",
        "Oracle",
        "MongoDB",
        "NoSQL",
        "Docker",
        "Kubernetes",
        "Git",
        "GitHub",
        "Maven",
        "Gradle",
        "Jenkins",
        "CI/CD",
        "AWS",
        "Azure",
        "GCP",
        "Kafka",
        "Redis",
        "React",
        "ReactJS",
        "Angular",
        "JavaScript",
        "TypeScript",
        "HTML",
        "CSS",
        "GraphQL",
        "Hibernate",
        "JPA",
        "JUnit",
        "Mockito",
        "Python",
        "Data Structures",
        "Algorithms",
        "System Design",
        "Agile",
        "Scrum",
        "Machine Learning",
        "Pandas",
        "NumPy",
        "TensorFlow",
        "PyTorch",
        "Linux"
    ]

    found = []

    for skill in skills:

        if skill.lower() in text_lower:

            found.append(
                normalize_skill(skill)
            )

    return sorted(
        list(set(found))
    )


def extract_keywords(text):

    if not text:
        return []

    words = re.findall(
        r"[A-Za-z][A-Za-z+#.-]{2,}",
        text.lower()
    )

    stop_words = {

        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "have",
        "has",
        "are",
        "was",
        "will",
        "your",
        "you",
        "our",
        "their",
        "into",
        "using",
        "used",
        "experience",
        "work",
        "working",
        "years",
        "year",
        "role",
        "developer",
        "engineer"

    }

    return sorted(
        set(
            word
            for word in words
            if word not in stop_words
        )
    )


def calculate_resume_score(
    resume_text,
    skills
):

    if not resume_text:
        return 0

    score = 0

    # Skills
    score += min(
        len(skills) * 5,
        50
    )

    # Basic resume sections
    sections = [

        "education",
        "experience",
        "project",
        "skills",
        "certification"

    ]

    text_lower = resume_text.lower()

    for section in sections:

        if section in text_lower:

            score += 8

    # Resume length
    if len(resume_text) > 1000:
        score += 10

    if len(resume_text) > 2500:
        score += 5

    return min(
        score,
        100
    )


def skill_level(score):

    if score < 3:
        return "Beginner"

    if score < 5:
        return "Developing"

    if score < 7:
        return "Intermediate"

    if score < 8.5:
        return "Strong"

    return "Advanced"


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({

        "status":
            "success",

        "message":
            "AI Career Interviewer backend is running."

    })


# =========================================================
# TEST DATABASE
# =========================================================

@app.route("/test-db")
def test_db():

    try:

        response = (
            supabase
            .table("users")
            .select("id")
            .limit(1)
            .execute()
        )

        return jsonify({

            "status":
                "success",

            "message":
                "Supabase connection working.",

            "data":
                response.data

        })

    except Exception as e:

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# LIVE JOBS
# =========================================================

@app.route("/api/jobs")
def get_jobs():

    try:

        role = request.args.get(
            "role",
            ""
        ).strip()

        location = request.args.get(
            "location",
            "India"
        ).strip()


        if not role:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Job role is required."

            }), 400


        results = serpapi_client.search({

            "engine":
                "google_jobs",

            "q":
                role,

            "location":
                location,

            "hl":
                "en",

            "gl":
                "in"

        })


        jobs = results.get(
            "jobs_results",
            []
        )


        saved_jobs = []


        for job in jobs[:10]:

            job_data = {

                "title":
                    job.get("title"),

                "company":
                    job.get("company_name"),

                "location":
                    job.get("location"),

                "description":
                    job.get(
                        "description",
                        ""
                    ),

                "source":
                    job.get("via"),

                "source_link":
                    job.get("share_link")

            }


            saved_jobs.append(
                job_data
            )


            try:

                (
                    supabase
                    .table("jobs")
                    .insert(job_data)
                    .execute()
                )

            except Exception as db_error:

                print(
                    "Job save warning:",
                    db_error
                )


        return jsonify({

            "status":
                "success",

            "jobs_found":
                len(jobs),

            "jobs":
                saved_jobs

        })


    except Exception as e:

        print(
            "Jobs error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# MARKET SKILLS
# =========================================================

@app.route("/api/skills")
def get_skills():

    try:

        role = request.args.get(
            "role",
            ""
        ).strip()


        response = (
            supabase
            .table("jobs")
            .select("*")
            .execute()
        )


        jobs = response.data or []


        if role:

            role_lower = role.lower()

            filtered = [

                job

                for job in jobs

                if role_lower
                in str(
                    job.get(
                        "title",
                        ""
                    )
                ).lower()

            ]

            if filtered:

                jobs = filtered


        skills = analyze_jobs(
            jobs
        )


        top_skills = get_top_skills(
            skills,
            limit=5
        )


        return jsonify({

            "status":
                "success",

            "skills":
                skills,

            "top_skills":
                top_skills

        })


    except Exception as e:

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# AI INTERVIEW
# =========================================================

@app.route("/api/interview")
def start_interview():

    try:

        role = request.args.get(
            "role",
            "Software Developer"
        ).strip()


        if not role:

            role = "Software Developer"


        jobs_response = (
            supabase
            .table("jobs")
            .select("*")
            .execute()
        )


        jobs = (
            jobs_response.data
            or []
        )


        role_lower = role.lower()


        filtered_jobs = [

            job

            for job in jobs

            if role_lower
            in str(
                job.get(
                    "title",
                    ""
                )
            ).lower()

        ]


        if not filtered_jobs:

            filtered_jobs = jobs


        skills = analyze_jobs(
            filtered_jobs
        )


        top_skills = get_top_skills(
            skills,
            limit=5
        )


        questions = generate_questions(
            role,
            top_skills
        )


        return jsonify({

            "status":
                "success",

            "role":
                role,

            "top_skills":
                top_skills,

            "questions":
                questions

        })


    except Exception as e:

        print(
            "Interview generation error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# ANSWER EVALUATION
# =========================================================

@app.route(
    "/api/evaluate",
    methods=["POST"]
)
def evaluate():

    try:

        data = request.get_json(
            silent=True
        ) or {}


        question = data.get(
            "question",
            ""
        ).strip()

        answer = data.get(
            "answer",
            ""
        ).strip()

        skill = data.get(
            "skill",
            ""
        ).strip()


        if not question:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Question is required."

            }), 400


        if not answer:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Answer is required."

            }), 400


        evaluation = evaluate_answer(
            question,
            answer,
            skill
        )


        return jsonify({

            "status":
                "success",

            "evaluation":
                evaluation

        })


    except Exception as e:

        print(
            "Evaluation error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# SKILL GAP
# =========================================================

@app.route(
    "/api/skill-gap",
    methods=["POST"]
)
def skill_gap():

    try:

        data = request.get_json(
            silent=True
        ) or {}


        evaluations = data.get(
            "evaluations",
            []
        )


        if not evaluations:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Evaluations are required."

            }), 400


        result = calculate_skill_gaps(
            evaluations
        )


        profile = result.get("skill_profile", []) if isinstance(result, dict) else result

        return jsonify({

            "status": "success",

            "skill_gaps": profile,

            "skill_profile": profile

        })


    except Exception as e:

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# SAVE INTERVIEW
# =========================================================

@app.route(
    "/api/interview/save",
    methods=["POST"]
)
def save_interview():

    try:

        user = require_user()

        user_db = g.user_supabase

        user_id = user.id


        data = request.get_json(
            silent=True
        ) or {}


        role = data.get(
            "role",
            ""
        )

        location = data.get(
            "location",
            ""
        )

        evaluations = data.get(
            "evaluations",
            []
        )


        if not evaluations:

            return jsonify({

                "error":
                    "No evaluations provided."

            }), 400


        scores = []


        for item in evaluations:

            evaluation = item.get(
                "evaluation",
                {}
            )


            score = evaluation.get(
                "score"
            )


            try:

                scores.append(
                    float(score)
                )

            except (
                TypeError,
                ValueError
            ):

                pass


        average_score = (

            round(
                sum(scores) /
                len(scores),
                2
            )

            if scores

            else 0

        )


        interview_response = (

            user_db
            .table("interviews")
            .insert({

                "user_id":
                    user_id,

                "role":
                    role,

                "location":
                    location,

                "total_score":
                    average_score

            })
            .execute()

        )


        if not interview_response.data:

            raise Exception(
                "Interview could not be saved."
            )


        interview_id = (
            interview_response
            .data[0]["id"]
        )


        questions_saved = 0
        answers_saved = 0


        for index, item in enumerate(
            evaluations
        ):

            question_text = item.get(
                "question",
                ""
            )

            user_answer = item.get(
                "answer",
                ""
            )

            skill = item.get(
                "skill",
                ""
            )

            evaluation = item.get(
                "evaluation",
                {}
            )

            score = evaluation.get(
                "score"
            )

            feedback = evaluation.get(
                "feedback",
                ""
            )


            question_response = (

                user_db
                .table("questions")
                .insert({

                    "interview_id":
                        interview_id,

                    "skill":
                        skill,

                    "question":
                        question_text,

                    "question_number":
                        index + 1

                })
                .execute()

            )


            question_id = None


            if question_response.data:

                questions_saved += 1

                question_id = (
                    question_response
                    .data[0]
                    .get("id")
                )


            answer_response = (

                user_db
                .table("answers")
                .insert({

                    "interview_id":
                        interview_id,

                    "question_id":
                        question_id,

                    "user_id":
                        user_id,

                    "answer":
                        user_answer,

                    "score":
                        score,

                    "feedback":
                        feedback,

                    "skill":
                        skill

                })
                .execute()

            )


            if answer_response.data:

                answers_saved += 1


        # -------------------------------------------------
        # PERSISTENT SKILL PROGRESS
        # -------------------------------------------------

        try:

            all_answers_response = (

                user_db
                .table("answers")
                .select(
                    "skill, score"
                )
                .eq(
                    "user_id",
                    user_id
                )
                .execute()

            )


            all_answers = (
                all_answers_response.data
                or []
            )


            grouped = {}


            for answer in all_answers:

                skill = answer.get(
                    "skill"
                )

                score = answer.get(
                    "score"
                )


                if not skill:

                    continue


                try:

                    score = float(score)

                except (
                    TypeError,
                    ValueError
                ):

                    continue


                skill = normalize_skill(
                    skill
                )


                grouped.setdefault(
                    skill,
                    []
                ).append(score)


            for skill, skill_scores in grouped.items():

                average = round(
                    sum(skill_scores) /
                    len(skill_scores),
                    2
                )


                level = skill_level(
                    average
                )


                existing = (

                    user_db
                    .table("skill_progress")
                    .select("*")
                    .eq(
                        "user_id",
                        user_id
                    )
                    .eq(
                        "skill",
                        skill
                    )
                    .execute()

                )


                if existing.data:

                    (
                        user_db
                        .table("skill_progress")
                        .update({

                            "score":
                                average,

                            "level":
                                level

                        })
                        .eq(
                            "id",
                            existing.data[0]["id"]
                        )
                        .execute()
                    )

                else:

                    (
                        user_db
                        .table("skill_progress")
                        .insert({

                            "user_id":
                                user_id,

                            "skill":
                                skill,

                            "score":
                                average,

                            "level":
                                level

                        })
                        .execute()
                    )


        except Exception as progress_error:

            print(
                "Skill progress warning:",
                progress_error
            )


        return jsonify({

            "status":
                "success",

            "interview_id":
                interview_id,

            "average_score":
                average_score,

            "questions_saved":
                questions_saved,

            "answers_saved":
                answers_saved

        })


    except Exception as e:

        print(
            "Save interview error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "error":
                str(e)

        }), 500


# =========================================================
# ROADMAP
# =========================================================

@app.route(
    "/api/roadmap",
    methods=["POST"]
)
def roadmap():

    try:

        data = request.get_json(
            silent=True
        ) or {}


        role = data.get(
            "role",
            "Software Developer"
        )

        skill_gaps = data.get(
            "skill_gaps",
            []
        )


        if not skill_gaps:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Skill gaps are required."

            }), 400


        roadmap_data = generate_roadmap(
            role,
            skill_gaps
        )


        return jsonify({

            "status":
                "success",

            "roadmap":
                roadmap_data

        })


    except Exception as e:

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/api/dashboard")
def dashboard():

    try:

        user = require_user()

        user_db = g.user_supabase

        user_id = user.id


        interviews_response = (

            user_db
            .table("interviews")
            .select("*")
            .eq(
                "user_id",
                user_id
            )
            .execute()

        )


        interviews = (
            interviews_response.data
            or []
        )

        interviews.sort(
            key=lambda item: item.get("created_at") or "",
            reverse=True
        )


        progress_response = (

            user_db
            .table("skill_progress")
            .select("*")
            .eq(
                "user_id",
                user_id
            )
            .order(
                "score",
                desc=True
            )
            .execute()

        )


        skill_progress = (
            progress_response.data
            or []
        )


        scores = []


        for interview in interviews:

            try:

                scores.append(
                    float(
                        interview.get(
                            "total_score",
                            0
                        )
                    )
                )

            except (
                TypeError,
                ValueError
            ):

                pass


        average_score = (

            round(
                sum(scores) /
                len(scores),
                1
            )

            if scores

            else 0

        )


        if average_score >= 8:

            career_level = "Interview Ready"

        elif average_score >= 6:

            career_level = "Strong"

        elif average_score >= 3:

            career_level = "Developing"

        else:

            career_level = "Beginner"


        return jsonify({

            "status":
                "success",

            "interview_count":
                len(interviews),

            "average_score":
                average_score,

            "skills_tracked":
                len(skill_progress),

            "skills":
                [
                    item.get("skill")
                    for item in skill_progress
                ],

            "skill_progress":
                skill_progress,

            "career_level":
                career_level,

            "latest_interview":
                interviews[0]
                if interviews
                else None

        })


    except Exception as e:

        return jsonify({

            "status":
                "error",

            "error":
                str(e)

        }), 500


# =========================================================
# INTERVIEW HISTORY
# =========================================================

@app.route("/api/interviews")
def get_interviews():

    try:

        user = require_user()

        user_db = g.user_supabase


        response = (

            user_db
            .table("interviews")
            .select("*")
            .eq(
                "user_id",
                user.id
            )
            .execute()

        )

        interviews = response.data or []
        interviews.sort(
            key=lambda item: item.get("created_at") or "",
            reverse=True
        )


        return jsonify({

            "status":
                "success",

            "interviews":
                interviews

        })


    except ValueError as e:
        print("Interview history auth error:", repr(e))
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 401

    except Exception as e:
        print("Interview history database error:", repr(e))
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# =========================================================
# INTERVIEW DETAILS
# =========================================================

@app.route(
    "/api/interviews/<interview_id>"
)
def get_interview_details(
    interview_id
):

    try:

        user = require_user()

        user_db = g.user_supabase


        interview_response = (

            user_db
            .table("interviews")
            .select("*")
            .eq(
                "id",
                interview_id
            )
            .eq(
                "user_id",
                user.id
            )
            .execute()

        )


        if not interview_response.data:

            return jsonify({

                "error":
                    "Interview not found."

            }), 404


        questions_response = (

            user_db
            .table("questions")
            .select("*")
            .eq(
                "interview_id",
                interview_id
            )
            .order(
                "question_number"
            )
            .execute()

        )


        answers_response = (

            user_db
            .table("answers")
            .select("*")
            .eq(
                "interview_id",
                interview_id
            )
            .order(
                "created_at"
            )
            .execute()

        )


        return jsonify({

            "status":
                "success",

            "interview":
                interview_response.data[0],

            "questions":
                questions_response.data
                or [],

            "answers":
                answers_response.data
                or []

        })


    except Exception as e:

        return jsonify({

            "status":
                "error",

            "error":
                str(e)

        }), 500


# =========================================================
# RESUME ANALYZER
# =========================================================

@app.route(
    "/api/resume/analyze",
    methods=["POST"]
)
def analyze_resume():

    try:

        user = require_user()

        user_db = g.user_supabase

        user_id = user.id


        data = request.get_json(
            silent=True
        ) or {}


        resume_text = data.get(
            "resume_text",
            ""
        ).strip()


        target_role = data.get(
            "target_role",
            ""
        ).strip()


        if not resume_text:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Resume text is required."

            }), 400


        resume_skills = (
            extract_resume_skills(
                resume_text
            )
        )


        resume_score = (
            calculate_resume_score(
                resume_text,
                resume_skills
            )
        )


        # -------------------------------------------------
        # Live market skills
        # -------------------------------------------------

        market_skills = []


        if target_role:

            try:

                jobs_response = (
                    user_db
                    .table("jobs")
                    .select("*")
                    .execute()
                )


                jobs = (
                    jobs_response.data
                    or []
                )


                role_jobs = [

                    job

                    for job in jobs

                    if target_role.lower()
                    in str(
                        job.get(
                            "title",
                            ""
                        )
                    ).lower()

                ]


                if role_jobs:

                    market = analyze_jobs(
                        role_jobs
                    )

                    market_skills = [

                        normalize_skill(
                            item["skill"]
                        )

                        for item
                        in get_top_skills(
                            market,
                            limit=10
                        )

                    ]

            except Exception:

                pass


        missing_skills = [

            skill

            for skill in market_skills

            if normalize_skill(skill)
            not in resume_skills

        ]


        strengths = resume_skills[:10]


        # -------------------------------------------------
        # Save
        # -------------------------------------------------

        (
            user_db
            .table("resume_analyses")
            .insert({

                "user_id":
                    user_id,

                "resume_text":
                    resume_text,

                "skills":
                    resume_skills,

                "score":
                    resume_score,

                "strengths":
                    strengths,

                "missing_skills":
                    missing_skills

            })
            .execute()
        )


        return jsonify({

            "status":
                "success",

            "score":
                resume_score,

            "skills":
                resume_skills,

            "strengths":
                strengths,

            "missing_skills":
                missing_skills,

            "target_role":
                target_role

        })


    except Exception as e:

        print(
            "Resume analysis error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# RESUME ↔ LIVE JOB MATCHING
# =========================================================

@app.route(
    "/api/jobs/match",
    methods=["POST"]
)
def match_jobs():

    try:

        user = require_user()

        user_db = g.user_supabase

        user_id = user.id


        data = request.get_json(
            silent=True
        ) or {}


        resume_skills = data.get(
            "resume_skills",
            []
        )


        role = data.get(
            "role",
            ""
        ).strip()


        location = data.get(
            "location",
            "India"
        ).strip()


        resume_skills = [

            normalize_skill(skill)

            for skill in resume_skills

        ]


        if not role:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Target role is required."

            }), 400


        results = serpapi_client.search({

            "engine":
                "google_jobs",

            "q":
                role,

            "location":
                location,

            "hl":
                "en",

            "gl":
                "in"

        })


        jobs = results.get(
            "jobs_results",
            []
        )


        matched_jobs = []


        for job in jobs[:10]:

            description = job.get(
                "description",
                ""
            )


            job_text = (

                str(
                    job.get(
                        "title",
                        ""
                    )
                )
                + " "
                + str(
                    description
                )

            )


            job_skills = extract_resume_skills(
                job_text
            )


            matched = [

                skill

                for skill in resume_skills

                if normalize_skill(skill)
                in job_skills

            ]


            missing = [

                skill

                for skill in job_skills

                if skill
                not in resume_skills

            ]


            if job_skills:

                match_score = round(

                    (
                        len(matched)
                        /
                        len(job_skills)
                    )
                    * 100,

                    1

                )

            else:

                match_score = 0


            job_result = {

                "title":
                    job.get(
                        "title"
                    ),

                "company":
                    job.get(
                        "company_name"
                    ),

                "location":
                    job.get(
                        "location"
                    ),

                "job_url":
                    job.get(
                        "share_link"
                    ),

                "match_score":
                    match_score,

                "matched_skills":
                    matched,

                "missing_skills":
                    missing[:10]

            }


            matched_jobs.append(
                job_result
            )


            try:

                match_row = {
                    "user_id": user_id,
                    "job_title": job_result.get("title"),
                    "company": job_result.get("company"),
                    "location": job_result.get("location"),
                    "job_url": job_result.get("job_url"),
                    "match_score": job_result.get("match_score", 0),
                    "matched_skills": job_result.get("matched_skills", []),
                    "missing_skills": job_result.get("missing_skills", [])
                }

                (
                    user_db
                    .table("job_matches")
                    .insert(match_row)
                    .execute()
                )

            except Exception as db_error:

                print(
                    "Job match save warning:",
                    db_error
                )


        matched_jobs.sort(
            key=lambda x:
                x["match_score"],
            reverse=True
        )


        return jsonify({

            "status":
                "success",

            "jobs":
                matched_jobs

        })


    except Exception as e:

        print(
            "Job matching error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# LEARNING RESOURCE SEARCH
# =========================================================

@app.route(
    "/api/resources",
    methods=["GET"]
)
def resources():

    try:

        user = require_user()

        user_db = g.user_supabase

        user_id = user.id


        skill = request.args.get(
            "skill",
            ""
        ).strip()


        if not skill:

            return jsonify({

                "status":
                    "error",

                "message":
                    "Skill is required."

            }), 400


        query = (
            f"{skill} tutorial course "
            f"documentation learning"
        )


        results = serpapi_client.search({

            "engine":
                "google",

            "q":
                query,

            "hl":
                "en",

            "gl":
                "in"

        })


        organic = results.get(
            "organic_results",
            []
        )


        resources_data = []


        for item in organic[:8]:

            resource = {

                "skill":
                    skill,

                "title":
                    item.get(
                        "title",
                        ""
                    ),

                "url":
                    item.get(
                        "link",
                        ""
                    ),

                "source":
                    item.get(
                        "source",
                        ""
                    ),

                "description":
                    item.get(
                        "snippet",
                        ""
                    )

            }


            resources_data.append(
                resource
            )


            try:

                (
                    user_db
                    .table(
                        "learning_resources"
                    )
                    .insert({

                        "user_id":
                            user_id,

                        **resource

                    })
                    .execute()
                )

            except Exception as db_error:

                print(
                    "Resource save warning:",
                    db_error
                )


        return jsonify({

            "status":
                "success",

            "skill":
                skill,

            "resources":
                resources_data

        })


    except Exception as e:

        print(
            "Resource search error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# CAREER INTELLIGENCE
# =========================================================

@app.route(
    "/api/career-intelligence"
)
def career_intelligence():

    try:

        user = require_user()

        user_db = g.user_supabase

        user_id = user.id


        # -------------------------------------------------
        # Profile
        # -------------------------------------------------

        profile_response = (

            user_db
            .table("users")
            .select("*")
            .eq(
                "id",
                user_id
            )
            .single()
            .execute()

        )


        profile = (
            profile_response.data
            or {}
        )


        role = profile.get(
            "target_role",
            ""
        )

        location = profile.get(
            "location",
            "India"
        )


        # -------------------------------------------------
        # Persistent skills
        # -------------------------------------------------

        progress_response = (

            user_db
            .table("skill_progress")
            .select("*")
            .eq(
                "user_id",
                user_id
            )
            .execute()

        )


        progress = (
            progress_response.data
            or []
        )


        # -------------------------------------------------
        # Live jobs
        # -------------------------------------------------

        jobs_result = serpapi_client.search({

            "engine":
                "google_jobs",

            "q":
                role
                if role
                else "Software Developer",

            "location":
                location,

            "hl":
                "en",

            "gl":
                "in"

        })


        jobs = jobs_result.get(
            "jobs_results",
            []
        )


        market_skills = []


        if jobs:

            market = analyze_jobs(
                jobs
            )

            market_skills = get_top_skills(
                market,
                limit=10
            )


        user_skill_names = [

            normalize_skill(
                item.get("skill", "")
            )

            for item in progress

        ]


        missing_market_skills = [

            item

            for item in market_skills

            if normalize_skill(
                item["skill"]
            )
            not in user_skill_names

        ]


        return jsonify({

            "status":
                "success",

            "role":
                role,

            "location":
                location,

            "live_jobs":
                len(jobs),

            "market_skills":
                market_skills,

            "your_skills":
                progress,

            "missing_market_skills":
                missing_market_skills

        })


    except Exception as e:

        print(
            "Career intelligence error:",
            e
        )

        return jsonify({

            "status":
                "error",

            "message":
                str(e)

        }), 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )