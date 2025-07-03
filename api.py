# api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os
import json
import requests

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
    # This is the same detailed prompt you designed earlier.
    return f"""
**Task**: Extract structured information from the resume text below and return ONLY valid JSON. Recognize alternative section names using these mappings:
{{
  "Contact": ["Personal Details", "Contact Information", "Get in Touch"],
  "Education": ["Academic Background", "Qualifications", "Degrees"],
  "Skills": ["Technical Skills", "Competencies", "Abilities"],
  "Experience": ["Work History", "Employment", "Professional Experience"],
  "Projects": ["Key Projects", "Major Projects", "Initiatives"]
}}

**Output Format**: 
{{
  "name": "Full Name",
  "contact": {{
    "phone": ["+1 234567890"],
    "email": ["name@domain.com"],
    "address": ["123 Main St, City"],
    "links": {{
      "linkedin": "https://linkedin.com/in/username",
      "github": "https://github.com/username",
      "portfolio": "https://personalwebsite.com"
    }}
  }},
  "education": [
    {{
      "degree": "Degree Name",
      "institution": "University Name",
      "dates": "YYYY-YYYY",
      "details": ["Relevant coursework/projects"]
    }}
  ],
  "skills": {{
    "technical": ["Python", "SQL"],
    "languages": ["English (Fluent)"],
    "tools": ["Git", "Docker"]
  }},
  "experience": [
    {{
      "position": "Job Title",
      "company": "Company Name",
      "dates": "YYYY-YYYY",
      "description": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief project summary",
      "technologies": ["Tech Stack"]
    }}
  ]
}}

**Instructions**:
1. Extract ALL available information in the exact JSON structure above.
2. Group content under headings using the alias mappings provided.
3. For lists (like skills, education, experience), capture ALL items.
4. Handle name variations: First/Last, Initials, Preferred names.
5. Normalize dates to YYYY-MM or YYYY format.
6. Capture ALL links (personal, social, project-related).
7. If a piece of information is not found, use a `null` value for the corresponding key.
8. NEVER add any explanatory text, comments, or apologies before or after the JSON output. Your entire response must be ONLY the JSON object.

**Resume Text**:
{resume_text}

"""

def clean_llm_output(text_output):
    """Extracts the JSON block from the LLM's raw text output."""
    try:
        # Find the start of the JSON object
        json_start_index = text_output.find('{')
        # Find the end of the JSON object
        json_end_index = text_output.rfind('}') + 1
        
        if json_start_index != -1 and json_end_index != -1:
            json_string = text_output[json_start_index:json_end_index]
            return json.loads(json_string)
        else:
            print("Warning: Could not find a JSON block in the output.")
            return None
    except json.JSONDecodeError:
        print("Error: Failed to decode the output into JSON.")
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
            max_tokens=2048,  # Max tokens to generate
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
