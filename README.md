Absolutely. Here is the **complete `README.md` again**, ready to copy and replace your existing file.

````markdown
# AI Career Interviewer

> Prepare for the jobs that are actually available right now.

AI Career Interviewer is an AI-powered career preparation platform that connects **live job-market requirements** with a user's **resume, interview performance, skill gaps, and personalized learning roadmap**.

Instead of preparing for generic interview questions, the application analyzes current job listings and helps users understand which skills employers are asking for, where their current gaps are, and what they should learn next.

---

## 🚀 Core Idea

Traditional interview preparation usually follows:

```text
Learn generic skills
        ↓
Practice generic questions
        ↓
Take an interview
````

AI Career Interviewer follows a market-driven approach:

```text
Live Job Listings
        ↓
Market Skill Analysis
        ↓
Resume Analysis
        ↓
Job Matching
        ↓
AI Interview
        ↓
AI Evaluation
        ↓
Unified Skill Gap
        ↓
Personalized Learning Roadmap
        ↓
Learning Resources
        ↓
Progress Tracking
```

---

# ✨ Features

## 🔐 Authentication

* User signup
* User login
* Supabase authentication
* Persistent user profile
* Target role and location

---

## 💼 Live Career Intelligence

The application uses **SerpApi Google Jobs** to retrieve current job listings for the user's target role and location.

The system analyzes job listings to identify frequently requested skills.

Example:

```text
Target Role: Java Developer
Location: Pune

Top Market Skills:
- Spring Boot
- Java
- SQL
- REST APIs
- Git
- AWS
```

This allows interview preparation to be connected to the current job market.

---

## 📄 Resume Analyzer

Users can upload their resume and analyze it against current market requirements.

The system extracts:

* Technical skills
* Strengths
* Missing market skills
* Resume score

The extracted skills are then used by the job-matching and skill-gap systems.

---

## 🎯 Job Matching

The application compares resume skills with skills identified from live job listings.

Each job receives a match percentage based on skill overlap.

Example:

```text
Java Backend Developer
Match: 60%

Matched:
- Java
- REST APIs
- Spring Boot

Missing:
- AWS
- Docker
- Kubernetes
```

This helps users understand which jobs align with their current profile.

---

## 🎤 AI Mock Interview

Users can practice interviews for their target role.

Interview questions are generated using:

* Target role
* Market-demanded skills
* Resume skills
* Identified skill gaps
* Experience level

The application supports interview categories such as:

* Technical Interview
* HR Interview
* Python Interview

The current career-intelligence flow focuses on market-driven technical preparation.

---

## 🤖 AI Answer Evaluation

User answers are evaluated by AI.

The evaluation considers factors such as:

* Correctness
* Relevance
* Technical understanding
* Completeness

The system provides:

* Score
* Feedback
* Improvement guidance

Interview results are stored for later review.

---

## 🧠 Unified Skill Gap Analysis

The Skill Gap system combines three signals:

```text
📄 Resume
     +
🎤 Interview Performance
     +
💼 Live Job Requirements
```

This creates a unified view of the user's development areas.

For example:

```text
AWS
Required by live jobs
Not present in resume
Interview not yet evaluated
→ Development area
```

Another example:

```text
Spring Boot
Present / evaluated
Interview score: 2/10
→ Interview performance needs improvement
```

The system also calculates market coverage based on the analyzed job requirements.

---

## 🗺️ AI Learning Roadmap

The application generates a personalized learning roadmap from the identified skill gaps.

The roadmap can contain:

* Weekly learning goals
* Topics
* Concepts
* Practice tasks
* Completion targets
* Role-specific learning priorities

Example:

```text
Week 1
REST API Fundamentals

Week 2
Spring Boot Architecture

Week 3
Spring Boot REST Services

Week 4
SQL + Advanced Git
```

The roadmap is designed around the user's actual development areas instead of a generic curriculum.

---

## 🔎 Learning Resources

Each roadmap skill can be searched for learning resources.

SerpApi is used to search the web for relevant:

* Tutorials
* Courses
* Documentation
* Learning material

Example:

```text
Spring Boot
      ↓
SerpApi Search
      ↓
Learning Resources
      ↓
Documentation / Tutorials / Courses
```

---

## 📊 Progress Tracking

The application tracks:

* Interviews completed
* Average interview score
* Skills practiced
* Skill performance
* Roadmap completion
* Latest interview
* Career-development progress

Users can review their progress over time.

---

## 📚 Interview History

Completed interviews are saved and can be viewed later.

Each interview contains:

* Role
* Date
* Overall score
* Questions
* Answers
* AI feedback
* Skill performance

---

# 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    │ HTML / CSS / JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Flask Backend     │
                    │      Python         │
                    └──────────┬──────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
      │   SerpApi   │   │   Gemini AI  │   │  Supabase   │
      │             │   │             │   │ PostgreSQL  │
      └─────────────┘   └─────────────┘   └─────────────┘
             │                 │                 │
             ▼                 ▼                 ▼
       Live Jobs          AI Questions      User Data
       Web Search         Evaluation        Interviews
                          Roadmaps           Skills
```

---

# 🧰 Technology Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* PDF.js
* Supabase JavaScript client

## Backend

* Python
* Flask
* REST APIs

## AI

* Google Gemini

Used for:

* Interview question generation
* Answer evaluation
* Learning roadmap generation

## Search / Market Intelligence

* SerpApi
* Google Jobs
* Google Search

## Database / Authentication

* Supabase
* PostgreSQL
* Supabase Authentication
* Row Level Security

## Development

* Git
* GitHub
* VS Code
* PowerShell

---

# 🔑 Environment Variables

Create:

```text
backend/.env
```

The file must NOT be committed to GitHub.

Example:

```env
SERPAPI_KEY=your_serpapi_key

SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key
SUPABASE_ANON_KEY=your_supabase_anon_key

GEMINI_API_KEY=your_gemini_api_key
```

Never publish real API keys.

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/rohitjagtap23/ai-mock-interview.git
```

Move into the project:

```bash
cd ai-mock-interview
```

---

# 🐍 Backend Setup

Open a terminal:

```powershell
cd backend
```

Create a virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create:

```text
backend/.env
```

and add the required API credentials.

Start the backend:

```powershell
python app.py
```

Backend:

```text
http://127.0.0.1:5000
```

---

# 🌐 Frontend Setup

Open another terminal:

```powershell
cd frontend
```

Start the local web server:

```powershell
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500/login.html
```

---

# 🔄 Application Workflow

## Step 1 — Create an account

Register using the signup page.

---

## Step 2 — Configure your career profile

Enter:

* Target role
* Location
* Experience level

---

## Step 3 — Analyze the market

The application uses SerpApi to retrieve live job listings.

The backend extracts frequently requested skills.

---

## Step 4 — Analyze your resume

Upload your resume.

The system extracts skills from the document.

---

## Step 5 — Match jobs

Your resume skills are compared against skills required by available jobs.

Each job receives a match score.

---

## Step 6 — Take the AI interview

The system generates questions based on your target role and market requirements.

---

## Step 7 — Receive AI evaluation

Submit answers and receive:

* Score
* Feedback
* Areas for improvement

---

## Step 8 — Analyze skill gaps

The system combines:

```text
Resume
Interview
Live Jobs
```

to create a unified skill profile.

---

## Step 9 — Generate learning roadmap

The AI generates a personalized learning plan based on the highest-priority development areas.

---

## Step 10 — Find learning resources

Search for tutorials, documentation and courses for roadmap skills.

---

## Step 11 — Track progress

Review:

* Interview history
* Skill progress
* Roadmap completion
* Career development

---

# 🔍 How SerpApi Is Used

SerpApi is a core part of the application.

It is used for two major workflows.

## 1. Live Job Market Intelligence

The application uses the Google Jobs engine to retrieve job listings based on:

```text
Target Role
+
Location
```

The resulting jobs are analyzed to identify market-demanded skills.

---

## 2. Learning Resource Discovery

SerpApi Google Search is used to discover learning resources for identified skill gaps.

Example query:

```text
Spring Boot tutorial course documentation learning
```

The application converts search results into learning-resource cards.

Therefore, SerpApi is part of the application's core career-intelligence workflow rather than a cosmetic integration.

---

# 🤖 AI Usage

Google Gemini is used for:

### Interview Question Generation

Generates role-specific technical interview questions using market skills.

### Answer Evaluation

Evaluates user responses and provides scores and feedback.

### Learning Roadmap

Generates structured learning plans based on identified skill gaps.

The application also contains deterministic fallback behavior for some AI-generated workflows when an AI request is temporarily unavailable.

---

# 🗄️ Database

Supabase PostgreSQL stores application data including:

```text
users
jobs
skills
job_skills
interviews
questions
answers
skill_progress
learning_plans
resume_analyses
job_matches
learning_resources
```

Authentication is handled through Supabase Auth.

User-specific data is protected using Row Level Security policies.

---

# 🔐 Security

Sensitive credentials are stored in:

```text
backend/.env
```

The environment file is excluded from Git through `.gitignore`.

The repository does not contain production API keys.

For deployment, environment variables should be configured through the hosting platform's secret-management system.

---

# 📁 Project Structure

```text
ai-mock-interview/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── skill_extractor.py
│   ├── question_generator.py
│   ├── answer_evaluator.py
│   ├── skill_gap.py
│   ├── roadmap_generator.py
│   ├── requirements.txt
│   ├── .gitignore
│   └── .env
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── career-intelligence.html
│   ├── resume.html
│   ├── job-matching.html
│   ├── job-match-details.html
│   ├── skill-gap.html
│   ├── roadmap.html
│   ├── progress.html
│   ├── interview-history.html
│   ├── interview-details.html
│   ├── learning-resources.html
│   ├── profile.html
│   ├── auth.js
│   ├── script.js
│   ├── page.js
│   └── style.css
│
├── README.md
└── .gitignore
```

---

# 🎯 Hackathon Track

**SerpApi India Hackathon 2026**

Selected track:

**Track 5 — Knowledge & Public Interest**

The project focuses on improving access to practical career and education information by connecting users with current job-market requirements, interview preparation, skill-gap analysis and learning resources.

---

# 🧪 Testing

The application has been tested locally across the primary workflow:

* Authentication
* Dashboard
* Career Intelligence
* Live job retrieval
* Resume analysis
* Job matching
* AI interviews
* AI evaluation
* Skill-gap analysis
* Learning roadmap
* Learning resources
* Interview history
* Progress tracking

Frontend:

```text
http://127.0.0.1:5500
```

Backend:

```text
http://127.0.0.1:5000
```

---

# 🏆 Project Value

The core idea is to move interview preparation from a generic approach toward a market-driven approach.

Instead of asking:

> "What interview questions should I practice?"

the system helps answer:

> "What skills are current employers asking for, how prepared am I, and what should I learn next?"

The result is a continuous career-preparation loop:

```text
Discover
   ↓
Analyze
   ↓
Practice
   ↓
Evaluate
   ↓
Identify Gaps
   ↓
Learn
   ↓
Track Progress
   ↓
Repeat
```

---

# 🔮 Future Improvements

Potential future improvements include:

* More interview categories
* Additional job-market sources
* Better resume-to-job semantic matching
* Advanced interview analytics
* More detailed skill progression
* Deployment for public access
* More learning-resource filtering
* Additional career paths

---

# 🤝 AI Tools Disclosure

AI-assisted development tools were used during development of this project for:

* Debugging
* Code generation
* Code review
* Feature implementation assistance
* Documentation
* Troubleshooting

The project functionality, integration decisions, testing and final implementation were reviewed and tested by the developer.

---

# 📌 Existing Project Disclosure

This project was started before the SerpApi India Hackathon.

The hackathon submission version contains meaningful work and integration with SerpApi, including:

* Live Google Jobs search
* Market skill extraction
* Career intelligence
* Learning-resource discovery

The SerpApi integration is part of the core functionality of the submitted version.

---

# 👨‍💻 Author

**Rohit Jagtap**

GitHub:

[https://github.com/rohitjagtap23](https://github.com/rohitjagtap23)

---
