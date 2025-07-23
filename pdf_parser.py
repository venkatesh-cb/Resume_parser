import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import docx2txt
import textract

def extract_text_and_links_from_pdf(pdf_path):
    """
    Extract both text and hyperlinks from a PDF file using PyMuPDF.
    """
    full_text = ""
    all_links = []

    try:
        with fitz.open(pdf_path) as doc:
            for page_number, page in enumerate(doc, start=1):
                # Extract visible text
                full_text += page.get_text()

                # Extract links (annotations or explicit URI links)
                links = page.get_links()
                for link in links:
                    if "uri" in link:
                        uri = link["uri"]
                        rect = fitz.Rect(link["from"])
                        linked_text = page.get_textbox(rect).strip()
                        all_links.append((linked_text, uri))

        # Append hyperlink references clearly at the end of the document
        if all_links:
            full_text += "\n\nExtracted Hyperlinks:\n"
            for idx, (text, uri) in enumerate(all_links, 1):
                display_text = f"{text} — {uri}" if text else uri
                full_text += f"[{idx}] {display_text}\n"

    except Exception as e:
        print(f"ERROR extracting from {pdf_path}: {e}")
        return ""

    return full_text

def extract_text_from_image(image_path):
    """
    Extract text from image using OCR (Tesseract).
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"ERROR extracting text from image {image_path}: {e}")
        return ""

def extract_text_from_docx(docx_path):
    """
    Extract text from .docx files.
    """
    try:
        return docx2txt.process(docx_path)
    except Exception as e:
        print(f"ERROR extracting text from DOCX {docx_path}: {e}")
        return ""

def extract_text_from_doc(doc_path):
    """
    Extract text from older .doc files using textract.
    """
    try:
        text = textract.process(doc_path).decode('utf-8')
        return text
    except Exception as e:
        print(f"ERROR extracting text from DOC {doc_path}: {e}")
        return ""

def extract_single_resume(file_path):
    """
    Determines file type and extracts text accordingly.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_and_links_from_pdf(file_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".doc":
        return extract_text_from_doc(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        return ""

def process_all_resumes(input_dir='resumes', output_dir='extracted_text'):
    """
    Batch process resumes of all supported formats in input_dir and save extracted text.
    """
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Created '{input_dir}' directory. Please add resumes there.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Processing resumes from '{input_dir}'...")
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"]:
            continue

        file_path = os.path.join(input_dir, filename)
        print(f"-> Processing: {filename}")
        extracted_text = extract_single_resume(file_path)

        if extracted_text.strip():
            txt_filename = os.path.splitext(filename)[0] + ".txt"
            output_path = os.path.join(output_dir, txt_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            print(f"Saved extracted content to '{output_path}'")
        else:
            print(f"Warning: No content extracted from '{filename}'.")

    print("✅ All resumes processed.")

if __name__ == '__main__':
    process_all_resumes()
