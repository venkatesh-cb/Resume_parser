# app.py

import streamlit as st
import os
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

            # st.success("✅ Text extracted. Sending to LLM...")

            with st.spinner("Parsing with LLM..."):
                parsed_data = parse_resume_text(extracted_text)

                if parsed_data:
                    json_path = os.path.join(PARSED_DIR, txt_filename.replace(".txt", ".json"))
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, indent=4)

                    # st.success("✅ Resume parsed successfully!")

                    # ------------------- Display Function ---------------------
                    def render_parsed_resume(data):
                        def render_field(label, value, indent=0):
                            if value in [None, "", [], {}]:
                                return
                            prefix = " " * indent

                            if isinstance(value, list):
                                if all(isinstance(item, str) for item in value):
                                    clean_label = label.strip() if label else ""
                                    if clean_label:
                                        st.markdown(f"{prefix}> **{clean_label}**:")
                                    for item in value:
                                        st.markdown(f"{prefix}&nbsp;&nbsp;&nbsp;&nbsp;- {item}")
                                else:
                                    clean_label = label.strip() if label else ""
                                    if clean_label:
                                        st.markdown(f"**{clean_label}**:")
                                    for i, item in enumerate(value):
                                        render_field("", item, indent + 4)
                                        if i < len(value) - 1:
                                            st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

                            elif isinstance(value, dict):
                                clean_label = label.strip() if label else ""
                                if clean_label:
                                    st.markdown(f"**{clean_label}**:")
                                for sub_label, sub_value in value.items():
                                    render_field(sub_label.replace("_", " ").title(), sub_value, indent + 4)

                            else:
                                clean_label = label.strip() if label else ""
                                if clean_label:
                                    st.markdown(f"{prefix}> **{clean_label}**: {value}")
                                else:
                                    st.markdown(f"{prefix}{value}")

                        # Print Name (if available at top)
                        if "name" in data:
                            st.markdown(f"### 👤 Name: {data['name']}")
                            del data["name"]

                        # Iterate and print each non-null section
                        for key, value in data.items():
                            if value in [None, "", [], {}]:
                                continue
                            section_title = key.replace("_", " ").title()
                            st.markdown(f"---\n### 📌 {section_title}")
                            render_field("", value)

                    # ------------------- Display Output ---------------------
                    st.subheader("📄 Resume Details: ")
                    render_parsed_resume(parsed_data)

                else:
                    st.error("❌ Failed to parse resume using LLM.")
