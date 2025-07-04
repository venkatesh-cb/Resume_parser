import os
import fitz  # PyMuPDF

def extract_text_and_links_from_pdf(pdf_path):
    """
    Extract both text and hyperlinks from a PDF file using PyMuPDF.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        str: Text content with inline hyperlinks and a section of extracted URLs at the end.
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
                        # Try to get the text near the link area
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


def process_all_resumes(input_dir='resumes', output_dir='extracted_text'):
    """
    Processes all PDF files in a given directory, extracts their text + links,
    and saves the enriched content to files in an output directory.
    """
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Created '{input_dir}' directory. Please add PDF resumes there.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Processing resumes from '{input_dir}'...")
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"-> Processing: {filename}")
            enriched_text = extract_text_and_links_from_pdf(pdf_path)

            if enriched_text.strip():
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(output_dir, txt_filename)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(enriched_text)
                print(f"Saved extracted content to '{output_path}'")
            else:
                print(f"Warning: No content extracted from '{filename}'.")
    print("✅ All resumes processed.")


if __name__ == '__main__':
    process_all_resumes()
