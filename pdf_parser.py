# pdf_parser.py

import os
import fitz  # PyMuPDF
import pdfplumber

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using both PyMuPDF and pdfplumber.
    It combines the strengths of both libraries for comprehensive extraction.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        str: The extracted text from the PDF.
    """
    text = ""
    try:
        # First, try extracting text with PyMuPDF
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        
        # If PyMuPDF returns very little or no text, try pdfplumber as a fallback
        if len(text.strip()) < 100: # Threshold can be adjusted
            print(f"PyMuPDF extracted little text from {os.path.basename(pdf_path)}. Trying PDFplumber as an alternative.")
            alt_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    alt_text += page.extract_text() or ""
            # Use the result that has more content
            if len(alt_text) > len(text):
                text = alt_text

    except Exception as e:
        print(f"Error processing file {pdf_path} with PyMuPDF: {e}")
        # If PyMuPDF fails, fall back completely to PDFplumber
        try:
            print(f"Falling back to PDFplumber for {os.path.basename(pdf_path)}.")
            text = "" # Reset text
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e_plumber:
            print(f"PDFplumber also failed for {pdf_path}: {e_plumber}")
            return None
            
    return text

def process_pdfs_in_directory(input_dir, output_dir):
    """
    Processes all PDF files in a given directory, extracts their text,
    and saves the text to files in an output directory.

    Args:
        input_dir (str): The directory containing PDF resumes.
        output_dir (str): The directory where extracted text will be saved.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing: {filename}")
            
            extracted_text = extract_text_from_pdf(pdf_path)
            
            if extracted_text and extracted_text.strip():
                # Create a corresponding .txt filename
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(output_dir, txt_filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                print(f"Successfully extracted text to: {output_path}")
            else:
                print(f"Could not extract text from {filename}. Skipping.")