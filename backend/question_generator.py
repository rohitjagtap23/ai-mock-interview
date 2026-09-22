import os,json,time
from dotenv import load_dotenv
from google import genai
load_dotenv(); key=os.getenv('GEMINI_API_KEY')
if not key: raise ValueError('GEMINI_API_KEY is missing from .env')
client=genai.Client(api_key=key)
MODELS=['gemini-3.5-flash-lite','gemini-3.6-flash','gemini-3.7-flash','gemini-3.8-flash']
def _json(text):
    text=(text or '').strip().replace('```json','').replace('```','').strip(); return json.loads(text)
def generate_questions(role,top_skills,resume_skills=None,missing_skills=None,experience_level='Beginner'):
    prompt=f'''Create exactly 5 technical interview questions for a candidate targeting {role}. Experience: {experience_level}. Market skills: {json.dumps(top_skills)}. Resume skills: {json.dumps(resume_skills or [])}. Missing skills: {json.dumps(missing_skills or [])}. Prioritize market demand, test practical understanding, include at least one missing skill, avoid repetition. Return only JSON array: [{{"skill":"Java","question":"..."}}]'''
    last=None
    for model in MODELS:
        try:
            r=client.models.generate_content(model=model,contents=prompt); data=_json(r.text)
            if isinstance(data,list) and len(data)>=5:
                return [dict(x,market_demand=True,personalized=True) for x in data[:5]]
        except Exception as e: last=e; time.sleep(.5)
    # Deterministic fallback keeps the demo usable if Gemini is temporarily unavailable.
    return [
        {"skill": "Java", "question": "Explain the four pillars of OOP in Java with a practical example.", "market_demand": True, "personalized": True},
        {"skill": "Spring Boot", "question": "How would you design a REST API in Spring Boot and handle validation and errors?", "market_demand": True, "personalized": True},
        {"skill": "SQL", "question": "How would you find the second-highest salary without using LIMIT? Explain your query.", "market_demand": True, "personalized": True},
        {"skill": "REST APIs", "question": "What makes an API RESTful and how would you secure a production REST API?", "market_demand": True, "personalized": True},
        {"skill": "System Design", "question": "Design a simple job-search service that can handle many concurrent users.", "market_demand": True, "personalized": True}
    ]
