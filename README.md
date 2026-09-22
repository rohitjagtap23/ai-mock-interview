# AI Career Interviewer — Final Clean Build

Core flow:

**Live jobs → market skills → personalized interview → AI evaluation → skill gaps → learning roadmap**

## Project structure

- `frontend/` — all browser pages and shared JavaScript/CSS
- `backend/` — Flask API, SerpApi integration, Gemini generation/evaluation, Supabase persistence

## Setup

### 1. Backend environment

Create `backend/.env` from `backend/.env.example`:

```env
SERPAPI_KEY=your_serpapi_key
SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key
GEMINI_API_KEY=your_gemini_api_key
```

Never put the Supabase secret/service-role key in frontend files.

### 2. Frontend Supabase key

Open `frontend/auth.js` and set:

```javascript
const SUPABASE_URL = 'YOUR_SUPABASE_URL';
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_PUBLIC_ANON_KEY';
```

The frontend uses only the public/anon key.

### 3. Install backend dependencies

```powershell
cd backend
python -m pip install -r requirements.txt
```

### 4. Start backend

```powershell
cd backend
python app.py
```

Backend: `http://127.0.0.1:5000`

### 5. Start frontend

Open a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Frontend: `http://127.0.0.1:5500/login.html`

## Features

- Supabase email authentication
- Profile management
- Live Google Jobs analysis through SerpApi
- Personalized text interview
- Browser voice interview
- AI answer evaluation
- Persistent interview history
- Skill-gap analysis
- Personalized learning roadmap
- Resume PDF extraction and analysis
- Resume-to-job matching
- Learning-resource search
- Career dashboard and progress

## Important

The AI features require working SerpApi/Gemini credentials and the Supabase schema used by the backend. If a third-party API is temporarily unavailable, the browser will show the API error instead of silently claiming success.

For the hackathon, keep `.env` local and do not commit it.
