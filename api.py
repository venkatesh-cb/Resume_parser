# api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os
import json
import requests
import re
# --- Configuration ---
# Using a quantized model from TheBloke, a reputable source for GGUF models.
MODEL_NAME = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
MODEL_FILE = "mistral-7b-instruct-v0.2.Q4_K_M.gguf" # 4-bit quantization, a good balance of size and quality
MODEL_PATH = f"./{MODEL_FILE}"

# Initialize FastAPI app
app = FastAPI()

# Global variable for the model
llm = None

# --- Pydantic Models for Request and Response ---
class ResumeRequest(BaseModel):
    resume_text: str

# --- Helper Functions ---
def download_model():
    """Downloads the GGUF model from Hugging Face if it doesn't exist."""
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found. Downloading {MODEL_FILE}...")
        url = f"https://huggingface.co/{MODEL_NAME}/resolve/main/{MODEL_FILE}"
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(MODEL_PATH, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print("Model downloaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to download model: {e}")

def get_llm_prompt(resume_text):
    """Constructs the detailed prompt for the LLM."""
    # Ensure this section is very clear and strict.
    return f"""
**Task**: Extract structured information from the resume text below.
**Strict Instruction**: You MUST ONLY return a single, complete, and valid JSON object. Do NOT include any additional text, explanations, or Markdown code block delimiters (like ```json or ```).
The JSON object should have the following keys (ensure these match exactly what you want):
{
    {
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "123-456-7890",
  "summary": "Professional summary...",
  "skills": ["Skill1", "Skill2"],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Start Date - End Date",
      "description": "Job responsibilities and achievements."
    }}
  ],
  "education": [
    {{
      "degree": "Degree Name",
      "university": "University Name",
      "graduation_year": "Year"
    }}
  ]
  }
}

**Resume Text**:
{resume_text}

"""

def clean_llm_output(text_output):
    """
    Extracts and cleans the JSON block from the LLM's raw text output.
    Handles Markdown code blocks and common LLM conversational filler.
    """
    try:
        # Step 1: Try to find a JSON block wrapped in ```json ... ```
        json_match = re.search(r'```json\n({.*?})\n```', text_output, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
            print("Found JSON in ```json``` block.")
            return json.loads(json_string)

        # Step 2: Try to find a JSON block wrapped in ``` ... ``` (without 'json' language specifier)
        json_match = re.search(r'```\n({.*?})\n```', text_output, re.DOTALL)
        if json_match:
            json_string = json_match.group(1)
            print("Found JSON in generic ``` block.")
            return json.loads(json_string)

        # Step 3: Fallback to finding the first { and last } (your original approach)
        # This is less robust but handles cases where no Markdown block is used.
        json_start_index = text_output.find('{')
        json_end_index = text_output.rfind('}') + 1
        
        if json_start_index != -1 and json_end_index != -1 and json_end_index > json_start_index:
            json_string = text_output[json_start_index:json_end_index]
            print("Found JSON by searching for {} bounds.")
            return json.loads(json_string)
        else:
            print("Warning: Could not find a valid JSON block in the output.")
            print(f"Raw LLM Output (first 500 chars): {text_output[:500]}") # Print part of output for debugging
            return None
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode the output into JSON. Details: {e}")
        print(f"Attempted JSON string:\n{json_string}") # Print the string that failed to decode
        print(f"Raw LLM Output (first 500 chars): {text_output[:500]}") # Print part of output for debugging
        return None
    except Exception as e:
        print(f"An unexpected error occurred in clean_llm_output: {e}")
        print(f"Raw LLM Output (first 500 chars): {text_output[:500]}") # Print part of output for debugging
        return None

# --- API Lifespan Events ---
@app.on_event("startup")
async def startup_event():
    """Code to run on server startup."""
    global llm
    print("Server starting up...")
    download_model()
    print("Loading LLM model. This may take a moment...")
    try:
        # Load the quantized model into memory
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,      # Context window size
            n_gpu_layers=0,  # Run on CPU. Set to -1 to offload all layers to GPU if available.
            verbose=False    # Set to True for detailed logs
        )
        print("Model loaded successfully.")
    except Exception as e:
        raise RuntimeError(f"Failed to load the Llama model: {e}")

# --- API Endpoints ---
@app.post("/parse-resume/")
async def parse_resume(request: ResumeRequest):
    """
    API endpoint to parse resume text.
    Accepts a POST request with {'resume_text': '...'}
    Returns the structured JSON.
    """
    if not llm:
        raise HTTPException(status_code=503, detail="Model is not loaded or failed to load.")

    print("Received request, generating prompt...")
    prompt = get_llm_prompt(request.resume_text)

    print("Sending prompt to LLM...")
    try:
        output = llm(
            prompt,
            max_tokens=4096,  # Max tokens to generate
            stop=["```"],       # Stop generation at the end of the text block
            echo=False        # Don't echo the prompt in the output
        )
        
        raw_text = output["choices"][0]["text"]
        print("Received raw output from LLM. Parsing JSON...")
        
        parsed_json = clean_llm_output(raw_text)

        if parsed_json:
            return parsed_json
        else:
            raise HTTPException(status_code=500, detail="Failed to parse valid JSON from model output.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during LLM processing: {e}")

@app.get("/")
def read_root():
    return {"status": "Resume Parser API is running."}
