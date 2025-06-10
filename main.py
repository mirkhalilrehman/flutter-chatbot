from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

import json
import difflib
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# Use API key from .env
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
with open('faq_data.json', 'r') as f:
    faq_data = json.load(f)

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")

# FastAPI app
app = FastAPI()

# Enable CORS for Flutter frontend (allow all for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to Flutter domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

def find_best_answer(user_question):
    questions = [faq["question"] for faq in faq_data]
    best_match = difflib.get_close_matches(user_question, questions, n=1, cutoff=0.5)
    if best_match:
        for faq in faq_data:
            if faq["question"] == best_match[0]:
                return faq["answer"]
    return None

def generate_prompt(user_question, best_answer):
    if best_answer:
        prompt = (
            "You are a professional and concise virtual assistant. "
            "Here is a factual answer from the FAQ:\n\n"
            f"FAQ Answer: {best_answer}\n\n"
            f"User Question: {user_question}\n"
            "Based on the FAQ answer above, rephrase it if necessary, but keep the tone formal, informative, and avoid exaggeration or emotional language. Be brief and to the point."
        )
    else:
        prompt = (
            "You are a professional virtual assistant.\n"
            f"The user asked: {user_question}\n"
            "No relevant FAQ answer was found. Reply politely and formally to let them know."
        )
    return prompt

@app.post("/ask")
def ask_question(request: QuestionRequest):
    best_answer = find_best_answer(request.question)
    prompt = generate_prompt(request.question, best_answer)
    response = model.generate_content(prompt)
    return {"response": response.text}
