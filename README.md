# Resume_parser
Server:
 ssh -i ~/.ssh/resume-parser-key.pem ubuntu@Change.ap-south-1.compute.amazonaws.com
 cd Resume_parser/
 source venv/bin/activate
 uvicorn api:app --host 0.0.0.0 --port 8000

Client:
 python3 client.py


Ran file:
1. Starting client to process files...
2025-07-04 12:23:26 - INFO - Client started. Processing files in 'extracted_text' directory.

--- Processing: Hitesh Sharma_resume 79.txt ---
Successfully parsed and saved to parsed_resumes/Hitesh Sharma_resume 79.json
2025-07-04 12:42:17 - INFO - Client finished processing files.

2. Starting client to process files...
2025-07-04 12:56:13 - INFO - Client started. Processing files in 'extracted_text' directory.

--- Processing: Vyankatesh Galande19[1].txt ---
Successfully parsed and saved to parsed_resumes/Vyankatesh Galande19[1].json
2025-07-04 13:18:53 - INFO - Client finished processing files.

3. Starting client to process files...
2025-07-04 13:25:17 - INFO - Client started. Processing files in 'extracted_text' directory.

--- Processing: 2211venkateshs@gmail.com.txt ---
Successfully parsed and saved to parsed_resumes/2211venkateshs@gmail.com.json
2025-07-04 13:37:46 - INFO - Client finished processing files.