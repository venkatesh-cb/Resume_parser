# Resume_parser
Server:
 ssh -i ~/.ssh/resume-parser-key.pem ubuntu@Change.ap-south-1.compute.amazonaws.com
 cd Resume_parser/
 source venv/bin/activate
 uvicorn api:app --host 0.0.0.0 --port 8000

Client:
 python3 client.py