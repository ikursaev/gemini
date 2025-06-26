import io
import json
import sys
import uuid
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from google import genai
import magic
import redis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from PIL import Image
from pydantic import BaseModel

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

temp_storage = {}

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    r = redis.asyncio.Redis(
        host=settings.REDIS_HOST, port=6379, db=0, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(r)
    yield


app = FastAPI(lifespan=lifespan)

# Configure the Gemini API
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

UPLOAD_FOLDER = settings.UPLOAD_FOLDER_NAME
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)


class Table(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class ExtractedData(BaseModel):
    text: str = ""
    tables: list[Table] = []


async def extract_content_from_image(
    image_bytes: bytes,
) -> tuple[ExtractedData, int, int]:
    try:
        image = Image.open(io.BytesIO(image_bytes))

        prompt_parts = [
            "Extract all text and any tables from this image. If tables are present, represent them as a JSON array of objects with 'headers' and 'rows' keys.",
            image,
        ]

        input_tokens = (await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[prompt_parts],
        ))
        response = await client.aio.models.generate_content(
            model=settings.MODEL_NAME,
            contents=[prompt_parts],
            config=genai.types.GenerateContentConfig(
                system_instruction="Extract all text and any tables from this image. Represent tables as a JSON array of objects with 'headers' and 'rows' keys.",
                temperature=0,
            ),
        )
        output_tokens = (await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[response.text],
        ))
        logger.info(
            f"Image Extraction - Input Tokens: {input_tokens}, Output Tokens: {output_tokens}"
        )
        # Attempt to parse as JSON first, then fallback to plain text
        try:
            data = response.text.strip()
            if data.startswith("```json") and data.endswith("```"):
                json_str = data[7:-3].strip()
                parsed_data = json.loads(json_str)
                return (
                    ExtractedData(
                        text=parsed_data.get("text", ""),
                        tables=[Table(**t) for t in parsed_data.get("tables", [])],
                    ),
                    input_tokens,
                    output_tokens,
                )
            else:
                return ExtractedData(text=response.text), input_tokens, output_tokens
        except json.JSONDecodeError:
            return ExtractedData(text=response.text), input_tokens, output_tokens
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")


def generate_markdown(extracted_data_list: list[ExtractedData]) -> str:
    markdown_output = ""
    for page_num, data in enumerate(extracted_data_list):
        if data.text:
            markdown_output += data.text + "\n\n"
        for i, table in enumerate(data.tables):
            markdown_output += f"## Table {i + 1} (Page {page_num + 1})\n\n"
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

    mime_type = magic.from_buffer(file_bytes, mime=True)

    if mime_type == "application/pdf":
        # Save the PDF to a temporary file
        temp_pdf_path = Path(UPLOAD_FOLDER) / file.filename
        with open(temp_pdf_path, "wb") as f:
            f.write(file_bytes)

        # Upload the file to Gemini
        uploaded_file = client.files.upload(file=temp_pdf_path)

        input_tokens = (await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[uploaded_file],
        ))

        # Generate content from the uploaded file
        response = await client.aio.models.generate_content(
            model=settings.MODEL_NAME,
            contents=[uploaded_file],
            config=genai.types.GenerateContentConfig(
                system_instruction="Extract all text and any tables from this PDF. Represent tables as a JSON array of objects with 'headers' and 'rows' keys.",
                temperature=0,
            ),
        )
        # Clean up the temporary file
        temp_pdf_path.unlink()

        output_tokens = (await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[response.text],
        ))

        logger.info(
            f"Image Extraction - Input Tokens: {input_tokens}, Output Tokens: {output_tokens}"
        )

        extracted_data_list = [ExtractedData(text=response.text)]
    elif mime_type.startswith("image/"):
        extracted_data, input_tokens, output_tokens = await extract_content_from_image(
            file_bytes
        )
        extracted_data_list = [extracted_data]  # Wrap in list for consistency
        logger.info(
            f"Total Input Tokens: {input_tokens}, Total Output Tokens: {output_tokens}"
        )
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported file type: {mime_type}"
        )

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


@app.get(
    "/download_markdown/{file_id}",
    dependencies=[Depends(RateLimiter(times=150, seconds=60))],
)
async def download_markdown(file_id: str):
    markdown_content = temp_storage.get(file_id)
    if not markdown_content:
        raise HTTPException(status_code=404, detail="File not found or expired.")

    return StreamingResponse(
        io.BytesIO(markdown_content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=extracted_data.md"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
