'''
import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from parser import extract_text_from_pdf
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-05-20",
    temperature=0.3
)

@app.post("/extract-claims")
async def extract_claims_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_bytes = await file.read()
    raw_text = extract_text_from_pdf(pdf_bytes)

    prompt = f"""
You are an expert claims data processor. Extract structured data from the following insurance document.

For each claim, return:
- Claim Number
- Accident Date
- Notice Date
- Close Date
- Incident Description

Return only a clean valid JSON array — no markdown, no comments, no backticks.

TEXT:
{raw_text}
"""

    try:
        response = llm.invoke(prompt)

        # Extract the actual content string from the AIMessage object
        result = response.content.strip()

        # Remove markdown if any
        if result.startswith("```json"):
            result = result.replace("```json", "").strip()
        if result.startswith("```"):
            result = result.replace("```", "").strip()
        if result.endswith("```"):
            result = result[:-3].strip()

        parsed = json.loads(result)
        return {"claims": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
'''

import os
import json
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
# Load .env and configure Gemini
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-05-20",
    temperature=0.3,
    google_api_key=api_key
)
# LangChain Prompt
prompt = PromptTemplate(
    input_variables=["pdf_text"],
    template="""
You are a professional form processor.
Extract structured information from this child care insurance application PDF content.
Output valid JSON grouped under these keys:
- Applicant Info
- Business Details
- Building Safety
- Staff & Children Info
- Health & Safety
- Sexual Abuse Policy
- Business Income
- Cybersecurity
- Signature Section
ONLY return clean JSON. Do not include any extra text or markdown.
Text:
{pdf_text}
"""
)
chain = LLMChain(llm=llm, prompt=prompt)
# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Function to extract text from PDF
def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Endpoint to extract structured claims JSON
@app.post("/extract-claims")
async def extract_claims_from_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        pdf_bytes = await file.read()
        raw_text = extract_text_from_pdf(pdf_bytes)

        result = chain.run(pdf_text=raw_text)

        # Optional: clean code fences if they exist
        if result.startswith("```json"):
            result = result.replace("```json", "").strip()
        if result.startswith("```"):
            result = result.replace("```", "").strip()
        if result.endswith("```"):
            result = result[:-3].strip()

        parsed_json = json.loads(result)
        return {"claims": parsed_json}

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM output was not valid JSON.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
