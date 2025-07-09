# api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os
import json
import requests
import re

# --- Configuration ---
MODEL_NAME = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
MODEL_FILE = "mistral-7b-instruct-v0.2.Q4_K_M.gguf" 
MODEL_PATH = f"./{MODEL_FILE}"

# Initialize FastAPI
app = FastAPI()
llm = None

# --- Request Schema ---
class ResumeRequest(BaseModel):
    resume_text: str

# --- Model Downloader ---
def download_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading {MODEL_FILE}...")
        url = f"https://huggingface.co/{MODEL_NAME}/resolve/main/{MODEL_FILE}"
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(MODEL_PATH, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("✅ Model downloaded.")
        except Exception as e:
            raise RuntimeError(f"Failed to download model: {e}")

# --- Prompt Generator ---
def get_llm_prompt(resume_text):
    return f"""
You are a smart resume parser.

Your task is to extract structured information from the resume text provided below. 
If the resume is messy, jumbled, or poorly formatted, interpret it to the best of your ability.
Use all available information to create a compact JSON response.

➤ Respond ONLY with valid JSON.
➤ Do NOT include comments, markdown, explanations, code blocks, or incomplete JSON.
➤ The response MUST begin with '{{' and end with '}}'.
➤ Every key should be in double quotes, as per standard JSON.
➤ Use lists for fields with multiple values.
➤ Omit fields that are not present.


Extractable fields:
- name
- contact: email, phone, linkedin, github, etc.
- summary(Include any messy or jumbled sentences)
- dob, gender, nationality
- education: degree, institute, location, dates, cgpa
- skills: group as programming_languages, tools, soft_skills
- certifications: title, issuer, date, certificate_link
- experience: job_title, company, location, dates, description, tools
- projects: title, tools, link, impact, description
- languages
- interests
- links (any URLs found)
- apps_built: name, platform, store_link
- achievements, publications, awards

Resume text:
\"\"\"
{resume_text}
\"\"\"

Respond only with JSON:
{{
  "name": "...",
  "contact": {{
    "email": "...",
    "phone": "...",
    "linkedin": "...",
    ...
  }},
  "summary": "...",
  "dob": "...",
  "gender": "...",
  "nationality": "...",
  "education": [...],
  "skills": {{
    "programming_languages": [...],
    "tools": [...],
    "soft_skills": [...]
  }},
  "certifications": [...],
  "experience": [...],
  "projects": [...],
  "languages": [...],
  "interests": [...],
  "links": [...],
  "apps_built": [...],
  "achievements": [...],
  "publications": [...]
}}
"""

# --- LLM Output Cleaner ---
def clean_llm_output(text_output):
    try:
        cleaned = re.sub(r"^\s*//.*$", "", text_output, flags=re.MULTILINE)
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            json_string = json_match.group()
            return json.loads(json_string)
        print("❌ No valid JSON block found.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSONDecodeError: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in clean_llm_output: {e}")
        return None

# --- Server Startup ---
@app.on_event("startup")
async def startup_event():
    global llm
    print("🚀 Starting up...")
    download_model()
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,
            n_gpu_layers=0,
            verbose=False
        )
        print("✅ Model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load Llama model: {e}")

# --- API Endpoint ---
@app.post("/parse-resume/")
async def parse_resume(request: ResumeRequest):
    if not llm:
        raise HTTPException(status_code=503, detail="Model is not loaded.")

    print("🔹 Received request.")
    prompt = get_llm_prompt(request.resume_text)

    try:
        output = llm(prompt, max_tokens=4096, stop=["```"], echo=False)
        raw_text = output["choices"][0]["text"]
        parsed_json = clean_llm_output(raw_text)

        if parsed_json:
            return parsed_json
        else:
            raise HTTPException(status_code=500, detail="Failed to parse valid JSON.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

@app.get("/")
def read_root():
    return {"status": "Resume Parser API is running."}
