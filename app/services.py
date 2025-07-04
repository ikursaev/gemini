import io
import json
import logging
from pathlib import Path

from fastapi import HTTPException
from google import genai
from PIL import Image
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class Table(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class ExtractedData(BaseModel):
    text: str = ""
    tables: list[Table] = []


client = genai.Client(api_key=settings.GOOGLE_API_KEY)


async def extract_content_from_image(
    image_bytes: bytes,
) -> tuple[ExtractedData, int, int]:
    try:
        image = Image.open(io.BytesIO(image_bytes))

        input_tokens = await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[image],
        )
        response = await client.aio.models.generate_content(
            model=settings.MODEL_NAME,
            contents=[image],
            config=genai.types.GenerateContentConfig(
                system_instruction="Extract all text from this image. Represent any tables as a JSON array of objects with 'headers' and 'rows' keys.",
                temperature=0,
            ),
        )
        output_tokens = await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[response.text or ""],
        )
        logger.info(
            f"Image Extraction - Input Tokens: {input_tokens}, Output Tokens: {output_tokens}"
        )
        # Attempt to parse as JSON first, then fallback to plain text
        try:
            data = (response.text or "").strip()
            if data.startswith("```json") and data.endswith("```"):
                json_str = data[7:-3].strip()
                parsed_data = json.loads(json_str)
                return (
                    ExtractedData(
                        text=parsed_data.get("text", ""),
                        tables=[Table(**t) for t in parsed_data.get("tables", [])],
                    ),
                    input_tokens.total_tokens or 0,
                    output_tokens.total_tokens or 0,
                )
            else:
                return (
                    ExtractedData(text=response.text or ""),
                    input_tokens.total_tokens or 0,
                    output_tokens.total_tokens or 0,
                )
        except json.JSONDecodeError:
            return (
                ExtractedData(text=response.text or ""),
                input_tokens.total_tokens or 0,
                output_tokens.total_tokens or 0,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")


async def extract_content_from_pdf(
    file_path: Path,
) -> tuple[list[ExtractedData], int, int]:
    try:
        # Upload the file to Gemini
        uploaded_file = client.files.upload(file=file_path)

        input_tokens = await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[uploaded_file],
        )

        # Generate content from the uploaded file
        response = await client.aio.models.generate_content(
            model=settings.MODEL_NAME,
            contents=[uploaded_file],
            config=genai.types.GenerateContentConfig(
                system_instruction="Extract all text from this PDF. Represent any tables as a JSON array of objects with 'headers' and 'rows' keys.",
                temperature=0,
            ),
        )

        output_tokens = await client.aio.models.count_tokens(
            model=settings.MODEL_NAME,
            contents=[response.text or ""],
        )

        logger.info(
            f"PDF Extraction - Input Tokens: {input_tokens}, Output Tokens: {output_tokens}"
        )

        try:
            data = (response.text or "").strip()
            if data.startswith("```json") and data.endswith("```"):
                json_str = data[7:-3].strip()
                parsed_data = json.loads(json_str)
                extracted_data_list = [
                    ExtractedData(
                        text=parsed_data.get("text", ""),
                        tables=[Table(**t) for t in parsed_data.get("tables", [])],
                    )
                ]
            else:
                extracted_data_list = [ExtractedData(text=response.text or "")]
        except json.JSONDecodeError:
            extracted_data_list = [ExtractedData(text=response.text or "")]

        return (
            extracted_data_list,
            input_tokens.total_tokens or 0,
            output_tokens.total_tokens or 0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")


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
