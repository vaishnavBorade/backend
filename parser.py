# /parser.py
from pypdf import PdfReader
import requests, io, os
from dotenv import load_dotenv

load_dotenv()
OCR_API_KEY = os.getenv("OCR_API_KEY")

def extract_text_from_pdf(file_bytes):
    try:
        pdf = PdfReader(io.BytesIO(file_bytes))
        text = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        if len(text.strip()) > 30:
            return text
    except: pass
    return extract_text_ocr(file_bytes)

def extract_text_ocr(file_bytes):
    r = requests.post(
        "https://api.ocr.space/parse/image",
        files={"file": ("resume.pdf", file_bytes)},
        data={"apikey": OCR_API_KEY},
    )
    try:
        return r.json()["ParsedResults"][0]["ParsedText"]
    except:
        return ""
