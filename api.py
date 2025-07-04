# api.py (Final version configured for TinyLlama)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os
import json
import requests
import re

# --- Configuration for TinyLlama ---
MODEL_NAME = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
MODEL_FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"  # Switched to a TinyLlama model file
MODEL_PATH = f"./{MODEL_FILE}"

# Initialize FastAPI app
app = FastAPI()

# Global variable for the model
llm = None

# --- Pydantic Models ---
class ResumeRequest(BaseModel):
    resume_text: str

# --- Helper Functions ---
def download_model():
    """Downloads the GGUF model from Hugging Face if it doesn't exist."""
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found. Downloading {MODEL_FILE}...")
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
    return f"""
Extract the following fields from the resume below and return only a JSON object: name, contact, education, skills, experience, projects. 
If any are missing, use null. Do not add explanations.

Resume:
{resume_text}

Format:
{{
  "name": "Full Name",
  "contact": "...",
  "education": [...],
  "skills": "...",
  "experience": [...],
  "projects": [...]
}}
"""


def clean_llm_output(text_output):
    match = re.search(r'{(?:[^{}]|(?R))*}', text_output, re.DOTALL)  # nested-safe JSON
    if match:
        json_string = match.group(0)
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
    else:
        print("No JSON found in output.")
        return None

# --- API Lifespan Events ---
@app.on_event("startup")
async def startup_event():
    """Code to run on server startup."""
    global llm
    print("Server starting up...")
    download_model()
    print("Loading TinyLlama model. This may take a moment...")
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,
            n_gpu_layers=0,
            verbose=False
        )
        print("Model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load the Llama model: {e}")

# --- API Endpoints ---
@app.post("/parse-resume/")
async def parse_resume(request: ResumeRequest):
    """API endpoint to parse resume text."""
    if not llm:
        raise HTTPException(status_code=503, detail="Model is not loaded or failed to load.")

    print("Received request, generating prompt...")
    prompt = get_llm_prompt(request.resume_text)

    print("Sending prompt to LLM...")
    try:
        output = llm(prompt, max_tokens=2048, stop=["```"], echo=False)
        raw_text = output["choices"][0]["text"]
        print("Received raw output from LLM. Parsing JSON...")
        print(f"--- RAW LLM OUTPUT ---\n{raw_text}\n----------------------")

        parsed_json = clean_llm_output(raw_text)

        if parsed_json:
            print("Successfully parsed JSON from output.")
            return parsed_json
        else:
            print(f"--- FAILED RAW OUTPUT ---\n{raw_text}\n-------------------------")
            with open("failed_output.txt", "w") as f:
                f.write(raw_text)
            raise HTTPException(status_code=500, detail="Server failed to parse a valid JSON response from the model.")

    except Exception as e:
        print(f"An error occurred during LLM processing: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during LLM processing: {e}")
    


@app.get("/")
def read_root():
    return {"status": "Resume Parser API is running."}
