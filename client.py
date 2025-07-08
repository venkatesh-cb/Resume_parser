# client.py

import requests
import os
import json
import datetime

# Replace with your EC2 instance's Public IPv4 address
SERVER_URL = "http://13.235.134.87:8000/parse-resume/"
TEXT_DIR = 'extracted_text'
OUTPUT_DIR = 'parsed_resumes'

def call_parser_api(resume_text):
    """Sends the resume text to the server and gets the JSON back."""
    try:
        response = requests.post(SERVER_URL, json={"resume_text": resume_text}, timeout=3600) # 60-minute timeout
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None

def main():
    """
    Main function to process all extracted text files through the API.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for filename in os.listdir(TEXT_DIR):
        if filename.endswith(".txt"):
            text_file_path = os.path.join(TEXT_DIR, filename)
            print(datetime.datetime.now())
            print(f"\n--- Processing: {filename} ---")

            with open(text_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                print("File is empty. Skipping.")
                continue

            parsed_data = call_parser_api(text)

            if parsed_data:
                json_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, json_filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, indent=4)
                print(f"Successfully parsed and saved to {output_path}")
            else:
                print(f"Failed to parse {filename}")
        print(datetime.datetime.now())

# For streamlit
def parse_resume_text(resume_text):
    return call_parser_api(resume_text)

# The corrected and simplified final block
if __name__ == "__main__":
    # This now directly calls your main function without any checks.
    print("Starting client to process files...")
    main()