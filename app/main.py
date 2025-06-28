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
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.config import settings
from app.tasks import process_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(settings.LOG_FILE_PATH), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

load_dotenv()

redis_client = redis.asyncio.Redis(
    host=settings.REDIS_HOST, port=6379, db=0, encoding="utf-8", decode_responses=True
)

TASK_LIST_KEY = "celery_tasks"  # Redis key to store task IDs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await FastAPILimiter.init(redis_client)
    yield


app = FastAPI(lifespan=lifespan)

UPLOAD_FOLDER = settings.UPLOAD_FOLDER_NAME
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/uploadfile/", dependencies=[Depends(RateLimiter(times=150, seconds=60))])
async def create_upload_file(file: UploadFile = File(...)):
    try:
        file_path = Path(UPLOAD_FOLDER) / file.filename
        # Ensure the UPLOAD_FOLDER exists
        Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        mime_type = magic.from_file(str(file_path), mime=True)

        task = process_file.delay(str(file_path), mime_type)
        await redis_client.lpush(TASK_LIST_KEY, task.id)  # Store task ID in Redis
        return JSONResponse({"task_id": task.id, "status": task.status})
    except Exception as e:
        logger.error(f"Error during file upload or task submission: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@app.get("/api/tasks")
async def get_all_tasks():
    task_ids = await redis_client.lrange(TASK_LIST_KEY, 0, -1)
    tasks = []
    for task_id in task_ids:
        task_result = AsyncResult(task_id)
        tasks.append({"id": task_id, "status": task_result.status})
    return JSONResponse(tasks)


@app.get("/api/tasks/{task_id}/result")
async def get_task_result_json(task_id: str):
    task_result = AsyncResult(task_id)
    if task_result.ready():
        result = task_result.get()
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return JSONResponse({"markdown": result["markdown"]})
    raise HTTPException(status_code=404, detail="Task not ready yet.")


@app.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    AsyncResult(task_id).revoke(terminate=True)
    return JSONResponse({"message": f"Task {task_id} stopped."})


@app.get(
    "/download_markdown/{task_id}",
    dependencies=[Depends(RateLimiter(times=150, seconds=60))],
)
async def download_markdown(task_id: str):
    task_result = AsyncResult(task_id)
    if not task_result.ready():
        raise HTTPException(status_code=404, detail="File not found or expired.")

    result = task_result.get()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    markdown_content = result["markdown"]

    return StreamingResponse(
        io.BytesIO(markdown_content.encode("utf-8")),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=extracted_data.md"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
