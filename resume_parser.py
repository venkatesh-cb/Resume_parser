# resume_parser.py (Updated and Corrected)

import os
import json
from transformers import pipeline
import torch

# It's highly recommended to log in via `huggingface-cli login`
# or set the HF_TOKEN environment variable for this to work.

# Define the model to use. google/gemma-2b-it is powerful and does not require gated access.
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" 
PIPE = None # Global pipeline object

def initialize_pipeline():
    """Initializes the LLM pipeline if it hasn't been already."""
    global PIPE
    if PIPE is None:
        try:
            print(f"Initializing LLM pipeline with model: {MODEL_NAME}...")
            PIPE = pipeline(
                "text-generation",
                model=MODEL_NAME,
                model_kwargs={"torch_dtype": torch.bfloat16}, # Use bfloat16 for better performance
                device_map="auto",
            )
            print("Pipeline initialized successfully.")
        except Exception as e:
            print(f"FATAL: Error initializing LLM pipeline: {e}")
            print("Please ensure you are logged into Hugging Face (`huggingface-cli login`) and have a stable internet connection.")
            # Set PIPE to an object that indicates failure to prevent retries
            PIPE = "failed" 

def get_llm_prompt(resume_text):
    """Constructs the detailed prompt for the LLM."""
    # This prompt structure is excellent. No changes needed here.
    # [The long prompt string you provided goes here. I'm omitting it for brevity,
    # but you should copy it from your original file or the previous response.]
    prompt = f"""
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
    return prompt


def parse_resume_text(resume_text):
    """
    Uses the LLM to parse resume text and extract structured JSON data.
    """
    # Step 1: Initialize the pipeline if it's not already loaded.
    initialize_pipeline()
    
    # Step 2: Check if initialization failed.
    if PIPE is None or PIPE == "failed":
        print("Cannot parse text because the LLM pipeline is not available.")
        return None

    # Step 3: Construct the prompt and generate text
    full_prompt = get_llm_prompt(resume_text)
    
    try:
        # The Gemma model family uses a specific chat template format.
        # We create this message list to get the best results.
        messages = [
            {"role": "user", "content": full_prompt},
        ]
        
        prompt_for_pipe = PIPE.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        outputs = PIPE(
            prompt_for_pipe,
            max_new_tokens=2048,
            do_sample=False, # Use do_sample=False and no temperature for more consistent JSON
        )
        
        generated_text = outputs[0]['generated_text']
        
        # Clean the output to find the JSON
        json_start_index = generated_text.find('{')
        json_end_index = generated_text.rfind('}') + 1
        
        if json_start_index != -1 and json_end_index != -1:
            json_string = generated_text[json_start_index:json_end_index]
            parsed_json = json.loads(json_string)
            return parsed_json
        else:
            print("Could not find valid JSON in the LLM output.")
            print("LLM Raw Output:", generated_text)
            return None

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM response: {e}")
        print("LLM Raw Output:", generated_text)
        return None
    except Exception as e:
        print(f"An error occurred during LLM processing: {e}")
        return None