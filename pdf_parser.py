import os
import fitz  # PyMuPDF


def extract_text_with_inline_links(pdf_path):
    """
    Extracts text and embeds hyperlinks inline next to the text (e.g., LinkedIn (https://...)).

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        str: Text content with inline hyperlinks.
    """
    output = ""

    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text = page.get_text("text")

                # Build a mutable version of the text
                for link in page.get_links():
                    if "uri" in link:
                        uri = link["uri"]
                        rect = fitz.Rect(link["from"])
                        linked_text = page.get_textbox(rect).strip()

                        if linked_text and linked_text in text:
                            # Replace first occurrence of linked_text with 'linked_text (url)'
                            replacement = f"{linked_text} ({uri})"
                            text = text.replace(linked_text, replacement, 1)

                output += text + "\n"

    except Exception as e:
        print(f"ERROR extracting from {pdf_path}: {e}")
        return ""

    return output


def process_all_resumes(input_dir='resumes', output_dir='extracted_text'):
    """
    Processes all PDF files in a given directory, extracts text + inline links,
    and saves them to .txt files.
    """
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Created '{input_dir}'. Add PDF resumes and rerun.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"📄 Processing resumes from '{input_dir}'...")
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"→ Processing: {filename}")
            extracted_text = extract_text_with_inline_links(pdf_path)

            if extracted_text.strip():
                output_file = os.path.splitext(filename)[0] + ".txt"
                output_path = os.path.join(output_dir, output_file)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)
                print(f"✅ Saved: {output_path}")
            else:
                print(f"⚠️ Skipped empty file: {filename}")
    print("🎉 All PDFs processed.")


if __name__ == '__main__':
    process_all_resumes()
