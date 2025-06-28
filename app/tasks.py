from celery import Celery
from app.services import extract_content_from_image, extract_content_from_pdf, generate_markdown
import magic
from pathlib import Path

celery = Celery(
    __name__,
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery.task
def process_file(file_path: str, mime_type: str):
    path = Path(file_path)
    if mime_type == "application/pdf":
        extracted_data_list, _, _ = extract_content_from_pdf(path)
    elif mime_type.startswith("image/"):
        with open(path, "rb") as f:
            file_bytes = f.read()
        extracted_data, _, _ = extract_content_from_image(file_bytes)
        extracted_data_list = [extracted_data]
    else:
        return {"error": f"Unsupported file type: {mime_type}"}

    markdown_content = generate_markdown(extracted_data_list)
    return {"markdown": markdown_content}
