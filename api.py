# api.py (fixed version)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os
import json
import requests
import re

# --- Model Setup ---
MODEL_NAME = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH = f"./{MODEL_FILE}"

app = FastAPI()
llm = None

class ResumeRequest(BaseModel):
    resume_text: str

def download_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading model {MODEL_FILE}...")
        url = f"https://huggingface.co/{MODEL_NAME}/resolve/main/{MODEL_FILE}"
        try:
            with requests.get(url, stream=True, timeout=600) as r:
                r.raise_for_status()
                with open(MODEL_PATH, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("Model downloaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to download model: {e}")

def get_llm_prompt(resume_text):
    # Very simplified prompt — TinyLlama cannot handle fancy instructions
    return f"""
Extract the following from the resume and respond ONLY with JSON: name, contact, education, skills, experience, projects.

Resume:
{resume_text}

Output:
{{"name": "", "contact": "", "education": [], "skills": "", "experience": [], "projects": []}}
"""

def clean_llm_output(text_output):
    """Extract first JSON-looking block from raw LLM output."""
    match = re.search(r'{.*}', text_output, re.DOTALL)
    if match:
        json_string = match.group(0)
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print("Trying fallback fix: remove trailing commas and retry...")
            try:
                cleaned = re.sub(r',(\s*[}\]])', r'\1', json_string)
                return json.loads(cleaned)
            except Exception as e:
                print(f"Still failed: {e}")
                return None
    print("No JSON found in output.")
    return None

@app.on_event("startup")
async def startup_event():
    global llm
    print("Server starting up...")
    download_model()
    print("Loading TinyLlama...")
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,
            n_gpu_layers=0,
            verbose=False
        )
        print("Model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Model loading failed: {e}")

@app.post("/parse-resume/")
async def parse_resume(request: ResumeRequest):
    if not llm:
        raise HTTPException(status_code=503, detail="Model not ready")

    prompt = get_llm_prompt(request.resume_text)
    print("Sending prompt to LLM...")

    try:
        output = llm(prompt, max_tokens=2048, stop=["```"], echo=False)
        raw_text = output["choices"][0]["text"]
        print(f"--- RAW LLM OUTPUT ---\n{raw_text}\n----------------------")

        parsed = clean_llm_output(raw_text)
        if parsed:
            return parsed
        else:
            raise HTTPException(status_code=500, detail="Model did not return valid JSON.")

    except Exception as e:
        print(f"LLM processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"status": "Resume Parser API running"}
