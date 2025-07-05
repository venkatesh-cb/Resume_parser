# app.py

import streamlit as st
import os
import shutil
import json
from pdf_parser import extract_single_resume
from client import parse_resume_text

# Directories
UPLOAD_DIR = "resumes"
TEXT_DIR = "extracted_text"
PARSED_DIR = "parsed_resumes"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)
os.makedirs(PARSED_DIR, exist_ok=True)

st.title("📄 Resume Parser using LLM")

uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

if uploaded_file:
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"Uploaded {uploaded_file.name}")

    with st.spinner("Extracting text and links from PDF..."):
        extracted_text = extract_single_resume(file_path)

        if not extracted_text.strip():
            st.error("No text found in the PDF.")
        else:
            # Save extracted text to extracted_text dir
            txt_filename = os.path.splitext(uploaded_file.name)[0] + ".txt"
            text_path = os.path.join(TEXT_DIR, txt_filename)
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

            st.success("✅ Text extracted. Sending to LLM...")

            with st.spinner("Parsing with LLM..."):
                parsed_data = parse_resume_text(extracted_text)

                if parsed_data:
                    json_path = os.path.join(PARSED_DIR, txt_filename.replace(".txt", ".json"))
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, indent=4)
                    
                    st.success("✅ Resume parsed successfully!")

                    def render_json_recursively(obj, level=1):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if level == 1:
                                    st.markdown(f"## {key}")
                                elif level == 2:
                                    st.markdown(f"### {key}")
                                elif level == 3:
                                    st.markdown(f"**{key}**")
                                else:
                                    st.markdown(f"- **{key}**")

                                render_json_recursively(value, level + 1)

                        elif isinstance(obj, list):
                            for item in obj:
                                render_json_recursively(item, level)

                        elif isinstance(obj, str):
                            st.markdown(f"{obj}")
                        
                    st.subheader("📌 Parsed Resume Data")
                    render_json_recursively(parsed_data)


                else:
                    st.error("❌ Failed to parse resume using LLM.")
