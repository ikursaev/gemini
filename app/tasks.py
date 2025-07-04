import asyncio
import logging
from pathlib import Path

from celery import Celery

from app.config import settings
from app.services import (
    extract_content_from_image,
    extract_content_from_pdf,
    generate_markdown,
)

logger = logging.getLogger(__name__)

# Use Redis URL from settings
celery = Celery(
    __name__,
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Configure Celery settings
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
)


@celery.task(bind=True, acks_late=True, reject_on_worker_lost=True)
def process_file(self, file_path: str, mime_type: str):
    """Process uploaded file and extract content."""
    task_id = self.request.id
    logger.info(f"Starting task {task_id} for file {file_path} with mime type {mime_type}")

    try:
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            logger.error(f"Task {task_id}: File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}

        # Process based on mime type
        if mime_type == "application/pdf":
            extracted_data_list, input_tokens, output_tokens = asyncio.run(extract_content_from_pdf(path))
        elif mime_type.startswith("image/"):
            with open(path, "rb") as f:
                file_bytes = f.read()
            extracted_data, input_tokens, output_tokens = asyncio.run(extract_content_from_image(file_bytes))
            extracted_data_list = [extracted_data]
        else:
            logger.error(f"Task {task_id}: Unsupported file type: {mime_type}")
            return {"error": f"Unsupported file type: {mime_type}"}

        # Generate markdown
        markdown_content = generate_markdown(extracted_data_list)

        # Clean up uploaded file after processing
        try:
            path.unlink(missing_ok=True)
            logger.info(f"Task {task_id}: Cleaned up uploaded file: {file_path}")
        except Exception as cleanup_error:
            logger.warning(f"Task {task_id}: Failed to cleanup file {file_path}: {cleanup_error}")

        logger.info(
            f"Task {task_id}: Successfully processed file. "
            f"Input Tokens: {input_tokens}, Output Tokens: {output_tokens}"
        )

        return {
            "markdown": markdown_content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    except Exception as e:
        logger.error(f"Task {task_id}: Error processing file {file_path}: {e}", exc_info=True)

        # Clean up file on error
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception:
            pass

        return {"error": str(e)}
