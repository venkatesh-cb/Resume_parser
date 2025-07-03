# main.py

import os
import json
from pdf_parser import process_pdfs_in_directory
from resume_parser import parse_resume_text

# Define the directories
RESUMES_DIR = 'resumes'
EXTRACTED_TEXT_DIR = 'extracted_text'
PARSED_RESUMES_DIR = 'parsed_resumes'

def main():
    """
    Main function to orchestrate the resume parsing pipeline.
    """
    print("--- Step 1: Extracting text from PDF resumes ---")
    process_pdfs_in_directory(RESUMES_DIR, EXTRACTED_TEXT_DIR)
    print("\n--- Text extraction complete ---")

    print("\n--- Step 2: Parsing extracted text with LLM ---")
    if not os.path.exists(PARSED_RESUMES_DIR):
        os.makedirs(PARSED_RESUMES_DIR)

    for filename in os.listdir(EXTRACTED_TEXT_DIR):
        if filename.endswith(".txt"):
            text_file_path = os.path.join(EXTRACTED_TEXT_DIR, filename)
            print(f"\nProcessing text file: {filename}")

            with open(text_file_path, 'r', encoding='utf-8') as f:
                resume_text = f.read()

            if not resume_text.strip():
                print(f"Text file {filename} is empty. Skipping.")
                continue

            parsed_data = parse_resume_text(resume_text)

            if parsed_data:
                # Save the structured data to a JSON file
                json_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(PARSED_RESUMES_DIR, json_filename)
                
                with open(output_path, 'w', encoding='utf-8') as json_file:
                    json.dump(parsed_data, json_file, indent=4)
                    
                print(f"Successfully parsed resume and saved to: {output_path}")
            else:
                print(f"Failed to parse resume from: {filename}")

    print("\n--- Resume parsing process finished ---")

if __name__ == "__main__":
    # Ensure necessary directories exist
    if not os.path.exists(RESUMES_DIR):
        os.makedirs(RESUMES_DIR)
        print(f"Created directory: {RESUMES_DIR}. Please add your PDF resumes here.")

    main()