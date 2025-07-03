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
        str: The extracted text from the PDF, or an empty string if extraction fails.
    """
    text = ""
    try:
        # First, try extracting text with PyMuPDF for its speed and accuracy with standard layouts.
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        
        # If PyMuPDF returns very little text, it might be a complex or image-based PDF.
        # In that case, we try pdfplumber as a fallback, as it can sometimes handle tables and complex layouts better.
        if len(text.strip()) < 100:  # Threshold can be adjusted based on expected resume length.
            print(f"INFO: PyMuPDF extracted little text from '{os.path.basename(pdf_path)}'. Trying PDFplumber as an alternative.")
            alt_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Fallback to an empty string if page.extract_text() returns None
                    alt_text += page.extract_text() or ""
            
            # Use the result from the library that extracted more content.
            if len(alt_text) > len(text):
                text = alt_text

    except Exception as e:
        print(f"ERROR: Could not process '{os.path.basename(pdf_path)}' with PyMuPDF. Error: {e}")
        # If PyMuPDF fails entirely, fall back completely to PDFplumber.
        try:
            print(f"INFO: Falling back to PDFplumber for '{os.path.basename(pdf_path)}'.")
            text = ""  # Reset text to ensure a clean slate
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e_plumber:
            print(f"FATAL: PDFplumber also failed for '{os.path.basename(pdf_path)}'. Error: {e_plumber}")
            return "" # Return empty string if both fail
            
    return text

def process_all_resumes(input_dir='resumes', output_dir='extracted_text'):
    """
    Processes all PDF files in a given directory, extracts their text,
    and saves the text to files in an output directory.

    Args:
        input_dir (str): The directory containing PDF resumes.
        output_dir (str): The directory where extracted text files will be saved.
    """
    # Create the input directory if it doesn't exist and inform the user.
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Created directory: '{input_dir}'. Please add your PDF resumes here.")
        return

    # Create the output directory if it doesn't exist.
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Starting PDF processing from '{input_dir}'...")
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"Processing: '{filename}'")
            
            extracted_text = extract_text_from_pdf(pdf_path)
            
            if extracted_text and extracted_text.strip():
                # Create a corresponding .txt filename.
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(output_dir, txt_filename)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                print(f"Successfully extracted text to: '{output_path}'")
            else:
                print(f"Warning: Could not extract any text from '{filename}'. Skipping.")
    print("PDF processing complete.")


if __name__ == '__main__':
    # This block makes the script runnable from the command line.
    process_all_resumes()