import logging
from pathlib import Path

from celery import Celery

from app.services import (
    extract_content_from_image,
    extract_content_from_pdf,
    generate_markdown,
)

logger = logging.getLogger(__name__)

celery = Celery(
    __name__,
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery.task(bind=True)
async def process_file(self, file_path: str, mime_type: str):
    logger.info(f"Starting task {self.request.id} for file {file_path} with mime type {mime_type}")
    try:
        path = Path(file_path)
        if mime_type == "application/pdf":
            extracted_data_list, input_tokens, output_tokens = await extract_content_from_pdf(path)
        elif mime_type.startswith("image/"):
            with open(path, "rb") as f:
                file_bytes = f.read()
            extracted_data, input_tokens, output_tokens = await extract_content_from_image(file_bytes)
            extracted_data_list = [extracted_data]
        else:
            logger.error(f"Task {self.request.id}: Unsupported file type: {mime_type}")
            return {"error": f"Unsupported file type: {mime_type}"}

        markdown_content = generate_markdown(extracted_data_list)
        logger.info(f"Task {self.request.id}: Successfully processed file. Input Tokens: {input_tokens}, Output Tokens: {output_tokens}")
        return {"markdown": markdown_content}
    except Exception as e:
        logger.error(f"Task {self.request.id}: Error processing file {file_path}: {e}", exc_info=True)
        return {"error": str(e)}
