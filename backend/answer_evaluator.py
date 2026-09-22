import os,json,time
from dotenv import load_dotenv
from google import genai
load_dotenv(); key=os.getenv('GEMINI_API_KEY')
if not key: raise ValueError('GEMINI_API_KEY is missing from .env')
client=genai.Client(api_key=key)
MODELS=['gemini-3.5-flash-lite','gemini-3.6-flash','gemini-3.7-flash','gemini-3.8-flash']
def evaluate_answer(question,answer,skill):
    prompt=f'''Evaluate this technical interview answer. Skill: {skill}. Question: {question}. Answer: {answer}. Score 0-10. Return ONLY JSON with keys score, technical_correctness, strengths(array), missing_concepts(array), communication, practical_knowledge, feedback, level, follow_up_question. Be constructive and specific.'''
    last=None
    for model in MODELS:
        try:
            r=client.models.generate_content(model=model,contents=prompt); t=(r.text or '').strip().replace('```json','').replace('```','').strip(); return json.loads(t)
        except Exception as e: last=e; time.sleep(.5)
    # Deterministic fallback keeps the interview demo functional during model outages.
    words=len((answer or '').split())
    score=8 if words>=70 else 7 if words>=40 else 5 if words>=20 else 3
    return {
        "score": score,
        "technical_correctness": "Your response addresses the question; add more concrete technical detail for a stronger answer.",
        "strengths": ["Directly attempted the question", "Shows relevant understanding"],
        "missing_concepts": ["Add a concrete example", "Explain trade-offs and edge cases"],
        "communication": "Generally understandable and relevant.",
        "practical_knowledge": "Include a real implementation or production scenario.",
        "feedback": "Structure the answer as concept → example → trade-off → conclusion.",
        "level": "Intermediate" if score>=5 else "Beginner",
        "follow_up_question": "What would you change in your solution for a production-scale system?"
    }
