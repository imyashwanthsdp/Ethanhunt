from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read token from .env
client = InferenceClient(
    token=os.getenv("HF_TOKEN")
)

class Query(BaseModel):
    topic: str

@app.get("/")
def home():
    return {"message": "Backend is running"}

@app.post("/research")
def research(query: Query):

    search_results = []

    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                query.topic,
                max_results=5
            )

            for r in results:
                search_results.append(
                    f"{r['title']} - {r['body']}"
                )

        context = "\n".join(search_results)

        prompt = f"""
        Research Topic:
        {query.topic}

        Sources:
        {context}

        Create a detailed report with:
        - Overview
        - Key Findings
        - Important Trends
        - Conclusion
        """

        response = client.chat_completion(
            model="Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000
        )

        return {
            "report": response.choices[0].message.content
        }

    except Exception as e:
        return {
            "error": str(e)
        }