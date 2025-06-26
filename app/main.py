import os
import io
import magic
import fitz
import sys
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
import json
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis
import uuid

temp_storage = {}

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup():
    r = redis.asyncio.Redis(host="localhost", port=6379, db=0, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)

# Configure the Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class Table(BaseModel):
    headers: list[str]
    rows: list[list[str]]

class ExtractedData(BaseModel):
    text: str = ""
    tables: list[Table] = []

async def extract_content_from_image(image_bytes: bytes) -> ExtractedData:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        response = await model.generate_content_async([
            "Extract all text and any tables from this image. Return beautifully formatted text as markdown, add formatting that better represents the title and contents of the text. If tables are present, represent them as a JSON array of objects with 'headers' and 'rows' keys.",
            image
        ])
        # Attempt to parse as JSON first, then fallback to plain text
        try:
            data = response.text.strip()
            if data.startswith("```json") and data.endswith("```"):
                json_str = data[7:-3].strip()
                parsed_data = json.loads(json_str)
                return ExtractedData(text=parsed_data.get("text", ""), tables=[Table(**t) for t in parsed_data.get("tables", [])])
            else:
                return ExtractedData(text=response.text)
        except json.JSONDecodeError:
            return ExtractedData(text=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

async def extract_content_from_pdf(pdf_bytes: bytes) -> list[ExtractedData]:
    extracted_pages_data = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content = page.get_text()
            tables_content = []

            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                extracted_image_data = await extract_content_from_image(image_bytes)
                text_content += "\n--- Image Text ---\n" + extracted_image_data.text
                tables_content.extend(extracted_image_data.tables)
            extracted_pages_data.append(ExtractedData(text=text_content, tables=tables_content))
        return extracted_pages_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")

def generate_markdown(extracted_data_list: list[ExtractedData]) -> str:
    markdown_output = ""
    for page_num, data in enumerate(extracted_data_list):
        markdown_output += f"# Page {page_num + 1}\n\n"
        if data.text:
            markdown_output += data.text + "\n\n"
        for i, table in enumerate(data.tables):
            markdown_output += f"## Table {i+1} (Page {page_num + 1})\n\n"
            markdown_output += "|" + "|".join(table.headers) + "|\n"
            markdown_output += "|" + "|".join(["---"] * len(table.headers)) + "|\n"
            for row in table.rows:
                markdown_output += "|" + "|".join(row) + "|\n"
            markdown_output += "\n"
        markdown_output += "---\n\n"  # Separator for pages
    return markdown_output

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("app/templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/uploadfile/", dependencies=[Depends(RateLimiter(times=150, seconds=60))])
async def create_upload_file(file: UploadFile = File(...)):
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    mime_type = magic.from_buffer(file_bytes, mime=True)

    if mime_type == "application/pdf":
        extracted_data_list = await extract_content_from_pdf(file_bytes)
    elif mime_type.startswith("image/"):
        extracted_data_list = [await extract_content_from_image(file_bytes)] # Wrap in list for consistency
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime_type}")

    markdown_content = generate_markdown(extracted_data_list)
    # Store the markdown content temporarily and generate a unique ID
    file_id = str(uuid.uuid4())
    temp_storage[file_id] = markdown_content

    with open("app/templates/result.html", "r") as f:
        html_content = f.read()
    
    # Replace placeholder with actual content and file_id
    html_content = html_content.replace("{{ text }}", markdown_content)
    html_content = html_content.replace("{{ file_id }}", file_id)
    
    return HTMLResponse(content=html_content)

@app.get("/download_markdown/{file_id}", dependencies=[Depends(RateLimiter(times=150, seconds=60))])
async def download_markdown(file_id: str):
    markdown_content = temp_storage.get(file_id)
    if not markdown_content:
        raise HTTPException(status_code=404, detail="File not found or expired.")
    
    return StreamingResponse(
        io.BytesIO(markdown_content.encode("utf-8")),
        media_type="text/markdown",
        headers={
            "Content-Disposition": "attachment; filename=extracted_data.md"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
