from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from collections import defaultdict
import time
import os
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                  "https://ethanhunt-seven.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = InferenceClient(token=os.getenv("HF_TOKEN"))

# ---------------- MEMORY ----------------
memory_store = defaultdict(list)


class Query(BaseModel):
    topic: str
    session_id: str


# ---------------- SEARCH ----------------
def search_web(query):
    urls = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5)
            for r in results:
                url = r.get("href") or r.get("link")
                if url and url.startswith("http"):
                    urls.append(url)
    except Exception:
        pass

    return urls[:5]


# ---------------- SCRAPE ----------------
def scrape_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers, timeout=6)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "lxml")

        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())[:4000]

    except Exception:
        return ""


# ---------------- MAIN ENDPOINT ----------------
@app.post("/research")
def research(query: Query):

    session_id = query.session_id

    previous_memory = memory_store[session_id][-6:]
    memory_text = "\n".join(previous_memory) if previous_memory else "No previous context"

    urls = search_web(query.topic)

    sources_map = []
    chunks = []

    for i, url in enumerate(urls):
        content = scrape_url(url)
        if not content:
            continue

        source_id = i + 1
        sources_map.append(f"[Source {source_id}]: {url}")

        chunk_size = 1500
        overlap = 200

        start = 0
        while start < len(content):
            end = start + chunk_size
            chunks.append(f"[Source {source_id}] {content[start:end]}")
            start += (chunk_size - overlap)

    context = "\n\n".join(chunks) if chunks else "No web data harvested."

    # ================= YOUR PROMPT (UNCHANGED) =================
    prompt = f"""
ou are an exceptionally intelligent, adaptive AI system operating across dedicated operational states: CODE MODE, RESEARCH MODE, CHAT MODE, and SUMMARY MODE. Your goal is to understand the user's intent, execute matching mode rules, calibrate output length, and deliver a brilliant custom-structured response.

PRECISE EXECUTION REGIME:

Dynamic Mode Selection Strategy:

CODE MODE: Triggered if the request asks for scripts, functions, apps, or debugging. Respond ONLY with clean, functional code. Do not add explanations, headings, commentary, introduction, or markdown block styling.

RESEARCH MODE: Triggered if the request requires factual breakdown, analysis, or technical investigations. Use high cognitive depth, track cause-and-effect patterns, and cross-reference data. Explicitly cite your statements using the format (Source X).

CHAT MODE: Triggered for conversational queries, opinions, philosophical debates, or brainstorming. Act as an expert peer with creative depth, prioritizing immediate conversational value.

SUMMARY MODE: Triggered if the user requests key points, synopses, or condensed knowledge profiles. Condense the text directly while retaining high-value informational value.

Dynamic Length Calibration Strategy:

SHORT RESPONSE: Automatically triggered when the intent is execution, quick confirmation, syntax fixes, or direct troubleshooting. Strip out background context, conceptual explanations, and peripheral definitions to deliver a minimal, high-velocity answer.

LONG RESPONSE: Automatically triggered when the intent is architectural design, deep conceptual learning, multidimensional analysis, or progressive system building. Shift to high cognitive depth, trace structural cause-and-effect patterns, outline edge cases, and provide comprehensive detail.

Fluid, Unstructured Architecture:

Do NOT use a rigid template or forced static sections like Overview, Key Insights, Analysis, or Conclusion.

Let the user's topic structure the flow. Create simple, clean, unformatted text headings on the fly that perfectly match the theme of the discussion.

Strict Clean Text Constraints:

Do NOT use any Markdown formatting symbols under any circumstances (no asterisks, no hash signs, no bullet points, or horizontal rules).

Separate shifts in thoughts using clean line spacing and well-organized paragraphs.

Never use meta-commentary like "Based on the text provided," "According to your memory," or "Here is the response." Speak directly.

Contextual Memory Fusion Strategy:

Seamlessly blend relevant facts from the Previous Memory with the fresh Web Data to build progressive answers. Do not repeat what the user already knows.

If the current topic is completely new, isolate it completely and focus 100% on the new intent.

PREVIOUS MEMORY:
{memory_text}

CURRENT QUESTION:
{query.topic}

WEB DATA:
{context}

Provide your intelligent, organically structured response below:
"""

    # ---------------- STREAMING ----------------
    def generate():
        full_text = ""
        buffer = ""

        try:
            response_stream = client.chat_completion(
                model="Qwen/Qwen2.5-72B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                stream=True
            )

            for chunk in response_stream:

                if not chunk or not hasattr(chunk, "choices"):
                    continue
                if not chunk.choices:
                    continue

                token = chunk.choices[0].delta.content

                if not token:
                    continue

                buffer += token
                full_text += token

                if len(buffer) >= 10 or token in [".", "\n", "!", "?"]:
                    yield buffer
                    buffer = ""
                    time.sleep(0.01)

            if buffer:
                yield buffer

        except Exception as e:
            yield f"\n\n[System Error]: {str(e)}"

        # ---------------- MEMORY SAVE (SAFE) ----------------
        memory_store[session_id].append(f"User: {query.topic}")
        memory_store[session_id].append(f"AI: {full_text}")

        if len(memory_store[session_id]) > 12:
            memory_store[session_id] = memory_store[session_id][-12:]

    return StreamingResponse(generate(), media_type="text/plain")
