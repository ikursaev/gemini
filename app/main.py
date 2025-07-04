import io
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import magic
import redis
from celery.result import AsyncResult
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.config import settings
from app.tasks import process_file
from app.utils import validate_file_size, validate_mime_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Redis client using settings
redis_client = redis.asyncio.Redis.from_url(
    settings.redis_url, encoding="utf-8", decode_responses=True
)

TASK_LIST_KEY = "celery_tasks"  # Redis key to store task IDs
TASK_TTL = 3600  # Task TTL in seconds (1 hour)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize FastAPI Limiter
    await FastAPILimiter.init(redis_client)
    logger.info("FastAPI Limiter initialized")

    # Ensure upload folder exists
    upload_path = Path(settings.UPLOAD_FOLDER_NAME)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload folder created: {upload_path}")

    yield

    # Cleanup on shutdown
    await redis_client.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Gemini Document Extractor",
    description="Extract text and tables from PDFs and images using Google's Gemini AI",
    version="0.1.0",
    lifespan=lifespan,
)

# Templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    health_status = {"status": "healthy", "components": {}}

    # Check Redis
    try:
        await redis_client.ping()
        health_status["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Check upload folder
    try:
        upload_path = Path(settings.UPLOAD_FOLDER_NAME)
        if upload_path.exists() and upload_path.is_dir():
            health_status["components"]["upload_folder"] = {"status": "healthy"}
        else:
            health_status["components"]["upload_folder"] = {
                "status": "unhealthy",
                "error": "Upload folder not accessible",
            }
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["components"]["upload_folder"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "unhealthy"

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/uploadfile/", dependencies=[Depends(RateLimiter(times=150, seconds=60))])
async def create_upload_file(file: UploadFile = File(...)):
    """Upload a file for processing with improved error handling and validation."""
    try:
        # Validate file size
        content = await file.read()
        file_size = len(content)

        # Use utility functions for validation
        is_valid_size, size_error = validate_file_size(file_size)
        if not is_valid_size:
            raise HTTPException(
                status_code=413 if "exceeds" in size_error else 400, detail=size_error
            )

        # Validate filename
        if not file.filename or file.filename.strip() == "":
            raise HTTPException(status_code=400, detail="No filename provided")

        # Use pathlib for better path handling
        upload_path = Path(settings.UPLOAD_FOLDER_NAME)
        upload_path.mkdir(parents=True, exist_ok=True)

        file_path = upload_path / file.filename

        # Write file content
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Detect MIME type
        mime_type = magic.from_file(str(file_path), mime=True)

        # Validate MIME type using utility function
        is_valid_mime, mime_error = validate_mime_type(mime_type)
        if not is_valid_mime:
            # Clean up uploaded file
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=mime_error)

        # Submit task for processing
        task = process_file.delay(str(file_path), mime_type)

        # Store task metadata in Redis with TTL
        import time

        task_metadata = {
            "task_id": task.id,
            "filename": file.filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "timestamp": int(time.time()),
            "status": task.status,
        }

        # Store task ID in list and metadata in hash
        await redis_client.lpush(TASK_LIST_KEY, task.id)
        await redis_client.expire(TASK_LIST_KEY, TASK_TTL)
        await redis_client.hset(f"task_metadata:{task.id}", mapping=task_metadata)
        await redis_client.expire(f"task_metadata:{task.id}", TASK_TTL)

        # Debug: verify the data was stored
        stored_metadata = await redis_client.hgetall(f"task_metadata:{task.id}")
        logger.info(f"Stored metadata for task {task.id}: {stored_metadata}")

        logger.info(
            f"File uploaded successfully: {file.filename}, Task ID: {task.id}, Size: {file_size} bytes"
        )

        return JSONResponse(
            {
                "task_id": task.id,
                "status": task.status,
                "filename": file.filename,
                "file_size": file_size,
                "mime_type": mime_type,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during file upload or task submission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/api/tasks")
async def get_all_tasks():
    """Get all tasks with their metadata and current status."""
    task_ids = await redis_client.lrange(TASK_LIST_KEY, 0, -1)
    tasks = []

    for task_id in task_ids:
        try:
            # Get current task status from Celery
            task_result = AsyncResult(task_id)
            current_status = task_result.status

            # Get task metadata from Redis
            metadata = await redis_client.hgetall(f"task_metadata:{task_id}")

            if metadata:
                # Convert timestamp to int if it exists
                if "timestamp" in metadata:
                    metadata["timestamp"] = int(metadata["timestamp"])

                # Update status with current status from Celery
                metadata["status"] = current_status
                metadata["task_id"] = task_id  # Ensure task_id is set

                tasks.append(metadata)
            else:
                # Fallback for tasks without metadata
                tasks.append(
                    {
                        "task_id": task_id,
                        "status": current_status,
                        "filename": "Unknown",
                        "timestamp": 0,
                    }
                )

        except Exception as e:
            logger.warning(f"Error processing task {task_id}: {e}")
            continue

    return JSONResponse(tasks)


@app.get("/api/tasks/{task_id}/result")
async def get_task_result_json(task_id: str):
    """Get task result as JSON."""
    try:
        task_result = AsyncResult(task_id)
        if task_result.ready():
            if task_result.successful():
                result = task_result.get()
                if result and isinstance(result, dict):
                    if "error" in result:
                        raise HTTPException(status_code=500, detail=result["error"])
                    if "markdown" in result:
                        return JSONResponse({"markdown": result["markdown"]})
                raise HTTPException(
                    status_code=500, detail="Invalid task result format"
                )
            else:
                # Task failed
                try:
                    task_result.get(propagate=True)
                except Exception as e:
                    raise HTTPException(
                        status_code=500, detail=f"Task failed: {str(e)}"
                    )
        raise HTTPException(status_code=404, detail="Task not ready yet.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task result for {task_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving task result: {str(e)}"
        )


@app.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    AsyncResult(task_id).revoke(terminate=True)
    return JSONResponse({"message": f"Task {task_id} stopped."})


@app.get(
    "/download_markdown/{task_id}",
    dependencies=[Depends(RateLimiter(times=150, seconds=60))],
)
async def download_markdown(task_id: str):
    """Download markdown result for a completed task."""
    try:
        task_result = AsyncResult(task_id)
        if not task_result.ready():
            raise HTTPException(status_code=404, detail="File not found or expired.")

        if not task_result.successful():
            raise HTTPException(
                status_code=500, detail="Task failed to complete successfully."
            )

        result = task_result.get()
        if not result or not isinstance(result, dict):
            raise HTTPException(status_code=500, detail="Invalid task result format.")

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        if "markdown" not in result:
            raise HTTPException(
                status_code=500, detail="No markdown content available."
            )

        markdown_content = result["markdown"]

        return StreamingResponse(
            io.BytesIO(markdown_content.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": "attachment; filename=extracted_data.md"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading markdown for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
