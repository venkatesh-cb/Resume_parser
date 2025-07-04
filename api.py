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
    """
    Constructs a more forceful and specific prompt for the LLM.
    """
    return f"""
**Task**: From the resume text below, extract structured information and return ONLY a valid JSON object.
**Instructions**:
1.  Extract all available information for the keys: name, contact, education, skills, experience, projects.
2.  Use the exact JSON structure provided in the format description.
3.  If information is missing, use null.
4.  Recognize alternate section names (e.g., "Work History" for "Experience").
5.  Your entire response must be a single JSON object. Start immediately with `{{` and end with `}}`. Do not add any introductory text, backticks, or explanations.

**Output Format**:
```json
{{
  "name": "Full Name",
  "contact": {{...}},
  "education": [{{...}}],
  "skills": {{...}},
  "experience": [{{...}}],
  "projects": [{{...}}]
}}
{resume_text}
"""

def clean_llm_output(text_output):
    """
    A more robust function to find and parse the JSON block from the LLM's raw text.
    It uses regular expressions to find the JSON object.
    """
    match = re.search(r'{.*}', text_output, re.DOTALL)

    if match:
        json_string = match.group(0)
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Error: Found a block that looks like JSON, but failed to decode. Error: {e}")
            print(f"--- Block Content ---\n{json_string}\n---------------------")
            return None
    else:
        print("Warning: Could not find a valid JSON block using regex.")
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

        parsed_json = clean_llm_output(raw_text)

        if parsed_json:
            print("Successfully parsed JSON from output.")
            return parsed_json
        else:
            print(f"--- FAILED RAW OUTPUT ---\n{raw_text}\n-------------------------")
            raise HTTPException(status_code=500, detail="Server failed to parse a valid JSON response from the model.")

    except Exception as e:
        print(f"An error occurred during LLM processing: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during LLM processing: {e}")

@app.get("/")
def read_root():
    return {"status": "Resume Parser API is running."}
