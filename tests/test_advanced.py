"""Advanced test suite for the Document Extractor application.

This module contains comprehensive tests covering:
- Configuration validation
- File processing pipeline
- Error handling scenarios
- Task management
- Redis integration
- API endpoint edge cases
"""

import asyncio
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import settings
from app.main import app
from app.services import ExtractedData, Table


class TestAdvancedConfiguration:
    """Advanced configuration and environment tests."""

    def test_config_validation_with_invalid_values(self):
        """Test configuration with invalid values."""
        # Test with invalid port
        with patch.dict("os.environ", {"PORT": "invalid_port"}):
            with pytest.raises(ValueError):
                from app.config import Settings

                Settings()

    def test_redis_connection_parameters(self):
        """Test Redis connection parameter formatting."""
        assert settings.REDIS_HOST is not None
        assert settings.REDIS_PORT > 0
        assert settings.REDIS_DB >= 0
        assert settings.redis_url.startswith("redis://")

    def test_upload_folder_creation(self):
        """Test that upload folder is properly configured."""
        assert settings.UPLOAD_FOLDER_NAME is not None
        assert len(settings.UPLOAD_FOLDER_NAME) > 0

    def test_security_settings(self):
        """Test security-related configuration."""
        assert settings.MAX_FILE_SIZE > 0
        assert settings.MAX_FILE_SIZE <= 100 * 1024 * 1024  # 100MB max
        assert settings.GOOGLE_API_KEY is not None


class TestFileValidationAdvanced:
    """Advanced file validation and security tests."""

    def test_validate_file_with_edge_cases(self):
        """Test file validation with edge case sizes."""
        from app.utils import validate_file_size

        # Test file at exact size limit
        is_valid, error = validate_file_size(settings.MAX_FILE_SIZE)
        assert is_valid is True

        # Test file one byte over limit
        is_valid, error = validate_file_size(settings.MAX_FILE_SIZE + 1)
        assert is_valid is False

        # Test negative file size
        is_valid, error = validate_file_size(-1)
        assert is_valid is False

    def test_mime_type_validation_comprehensive(self):
        """Test comprehensive MIME type validation."""
        from app.utils import validate_mime_type

        # Test all supported types
        supported_types = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]

        for mime_type in supported_types:
            is_valid, error = validate_mime_type(mime_type)
            assert is_valid is True, f"Failed for {mime_type}: {error}"

        # Test unsupported types
        unsupported_types = [
            "text/plain",
            "application/json",
            "video/mp4",
            "audio/mp3",
            "application/msword",
        ]

        for mime_type in unsupported_types:
            is_valid, error = validate_mime_type(mime_type)
            assert is_valid is False, f"Should fail for {mime_type}"

    def test_file_size_formatting_precision(self):
        """Test file size formatting with various precisions."""
        from app.utils import format_file_size

        test_cases = [
            (0, "0 B"),
            (1, "1.0 B"),
            (1023, "1023.0 B"),
            (1024, "1.0 KB"),
            (1536, "1.5 KB"),
            (1048576, "1.0 MB"),
            (1572864, "1.5 MB"),
            (1073741824, "1.0 GB"),
        ]

        for size, expected in test_cases:
            result = format_file_size(size)
            assert result == expected, f"Size {size}: expected {expected}, got {result}"


class TestAPIEndpointsAdvanced:
    """Advanced API endpoint testing with edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        return TestClient(app)

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for testing."""
        with patch("app.main.redis_client") as mock:
            mock.ping = AsyncMock(return_value=True)
            mock.lpush = AsyncMock()
            mock.expire = AsyncMock()
            mock.lrange = AsyncMock(return_value=[])
            mock.get = AsyncMock(return_value=None)
            yield mock

    def test_health_check_with_redis_failure(self, client):
        """Test health check when Redis is down."""
        with patch("app.main.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(
                side_effect=Exception("Redis connection failed")
            )
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis"] == "disconnected"

    def test_detailed_health_check(self, client, mock_redis):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "system_info" in data
        assert "disk_usage" in data
        assert "memory_usage" in data
        assert "redis_status" in data

    @patch("app.main.process_file")
    @patch("app.main.magic")
    def test_upload_file_with_task_creation_failure(
        self, mock_magic, mock_process_file, client, mock_redis
    ):
        """Test file upload when task creation fails."""
        mock_magic.from_file.return_value = "application/pdf"
        mock_process_file.delay.side_effect = Exception("Celery connection failed")

        test_file_content = b"test pdf content"
        response = client.post(
            "/uploadfile/",
            files={"file": ("test.pdf", test_file_content, "application/pdf")},
        )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to create processing task" in data["detail"]

    def test_upload_file_with_invalid_mime_detection(self, client, mock_redis):
        """Test upload when MIME type detection fails."""
        with patch("app.main.magic") as mock_magic:
            mock_magic.from_file.side_effect = Exception("Magic detection failed")

            response = client.post(
                "/uploadfile/",
                files={"file": ("test.pdf", b"content", "application/pdf")},
            )

            assert response.status_code == 500

    def test_task_status_endpoint_comprehensive(self, client, mock_redis):
        """Test task status endpoint with various scenarios."""
        # Test with valid task
        with patch("app.main.AsyncResult") as mock_result:
            mock_task = MagicMock()
            mock_task.status = "SUCCESS"
            mock_task.result = {
                "markdown": "# Test",
                "tokens": {"input": 100, "output": 50},
            }
            mock_result.return_value = mock_task

            response = client.get("/api/tasks/test-task-id/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "SUCCESS"

        # Test with failed task
        with patch("app.main.AsyncResult") as mock_result:
            mock_task = MagicMock()
            mock_task.status = "FAILURE"
            mock_task.result = Exception("Task failed")
            mock_result.return_value = mock_task

            response = client.get("/api/tasks/test-task-id/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "FAILURE"

    def test_download_markdown_edge_cases(self, client, mock_redis):
        """Test markdown download with edge cases."""
        # Test with non-existent task
        with patch("app.main.AsyncResult") as mock_result:
            mock_task = MagicMock()
            mock_task.status = "PENDING"
            mock_result.return_value = mock_task

            response = client.get("/download_markdown/nonexistent-task")
            assert response.status_code == 400
            assert "not completed" in response.json()["detail"]

        # Test with task that has no result
        with patch("app.main.AsyncResult") as mock_result:
            mock_task = MagicMock()
            mock_task.status = "SUCCESS"
            mock_task.result = None
            mock_result.return_value = mock_task

            response = client.get("/download_markdown/empty-result-task")
            assert response.status_code == 500

    def test_tasks_list_endpoint(self, client, mock_redis):
        """Test tasks list endpoint functionality."""
        # Mock Redis to return task IDs
        mock_redis.lrange.return_value = ["task1", "task2", "task3"]

        # Mock individual task metadata
        task_metadata = {
            "task1": json.dumps(
                {"filename": "test1.pdf", "timestamp": 1625097600, "status": "SUCCESS"}
            ),
            "task2": json.dumps(
                {"filename": "test2.png", "timestamp": 1625097700, "status": "PENDING"}
            ),
            "task3": None,  # Missing metadata
        }

        async def mock_get(key):
            return task_metadata.get(key.split(":")[-1])

        mock_redis.get = AsyncMock(side_effect=mock_get)

        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Should filter out task3 with missing metadata


class TestTaskProcessingAdvanced:
    """Advanced task processing tests."""

    @pytest.fixture
    def temp_pdf_file(self):
        """Create a temporary PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"%PDF-1.4 test content")
            temp_path = Path(tmp.name)
        yield temp_path
        temp_path.unlink(missing_ok=True)

    @pytest.fixture
    def temp_image_file(self):
        """Create a temporary image file for testing."""
        image = Image.new("RGB", (100, 100), color="red")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp, "PNG")
            temp_path = Path(tmp.name)
        yield temp_path
        temp_path.unlink(missing_ok=True)

    @patch("app.tasks.extract_content_from_pdf")
    @patch("app.tasks.generate_markdown")
    async def test_process_pdf_with_complex_content(
        self, mock_generate, mock_extract, temp_pdf_file
    ):
        """Test PDF processing with complex extracted content."""
        from app.tasks import process_file

        # Mock complex extraction result
        complex_data = ExtractedData(
            text="Complex document with multiple sections",
            tables=[
                Table(headers=["Col1", "Col2"], rows=[["A", "B"], ["C", "D"]]),
                Table(headers=["Name", "Value"], rows=[["Test", "123"]]),
            ],
        )
        mock_extract.return_value = (complex_data, 500, 250)
        mock_generate.return_value = "# Complex Document\n\n## Tables\n\n..."

        mock_task = MagicMock()
        mock_task.request.id = str(uuid4())

        result = await process_file.__wrapped__(
            mock_task, str(temp_pdf_file), "application/pdf"
        )

        assert "markdown" in result
        assert "tokens" in result
        assert result["tokens"]["input"] == 500
        assert result["tokens"]["output"] == 250
        assert "error" not in result

    @patch("app.tasks.extract_content_from_image")
    @patch("app.tasks.generate_markdown")
    async def test_process_image_with_extraction_failure(
        self, mock_generate, mock_extract, temp_image_file
    ):
        """Test image processing when extraction fails."""
        from app.tasks import process_file

        # Mock extraction failure
        mock_extract.side_effect = Exception("OCR failed")

        mock_task = MagicMock()
        mock_task.request.id = str(uuid4())

        result = await process_file.__wrapped__(
            mock_task, str(temp_image_file), "image/png"
        )

        assert "error" in result
        assert "OCR failed" in result["error"]

    async def test_process_file_with_corrupted_file(self):
        """Test processing with corrupted file."""
        from app.tasks import process_file

        # Create corrupted file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"corrupted content")
            corrupted_path = Path(tmp.name)

        try:
            mock_task = MagicMock()
            mock_task.request.id = str(uuid4())

            with patch("app.tasks.extract_content_from_pdf") as mock_extract:
                mock_extract.side_effect = Exception("Corrupted PDF")

                result = await process_file.__wrapped__(
                    mock_task, str(corrupted_path), "application/pdf"
                )

                assert "error" in result
                assert "Corrupted PDF" in result["error"]

        finally:
            corrupted_path.unlink(missing_ok=True)

    def test_celery_task_configuration(self):
        """Test Celery task configuration."""
        from app.tasks import celery

        assert celery.conf.task_serializer == "json"
        assert celery.conf.result_serializer == "json"
        assert celery.conf.result_expires == 3600
        assert celery.conf.timezone == "UTC"

    def test_run_async_safely_function(self):
        """Test the run_async_safely utility function."""
        from app.tasks import run_async_safely

        async def test_coroutine():
            return "success"

        result = run_async_safely(test_coroutine())
        assert result == "success"

        # Test with exception
        async def failing_coroutine():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_async_safely(failing_coroutine())


class TestServiceLayerAdvanced:
    """Advanced service layer testing."""

    @patch("app.services.client")
    async def test_pdf_extraction_with_timeout(self, mock_client):
        """Test PDF extraction with timeout scenarios."""
        from app.services import extract_content_from_pdf

        # Mock timeout scenario
        mock_client.aio.files.upload.side_effect = asyncio.TimeoutError(
            "Request timeout"
        )

        pdf_bytes = b"%PDF-1.4 test content"

        with pytest.raises(asyncio.TimeoutError):
            await extract_content_from_pdf(pdf_bytes)

    @patch("app.services.client")
    async def test_image_extraction_with_api_error(self, mock_client):
        """Test image extraction with API errors."""
        from app.services import extract_content_from_image

        # Mock API error
        mock_client.aio.models.generate_content.side_effect = Exception(
            "API rate limit exceeded"
        )

        # Create test image bytes
        image = Image.new("RGB", (100, 100), color="blue")
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        image_bytes = img_buffer.getvalue()

        with pytest.raises(Exception, match="API rate limit exceeded"):
            await extract_content_from_image(image_bytes)

    @patch("app.services.client")
    async def test_markdown_generation_with_complex_data(self, mock_client):
        """Test markdown generation with complex extracted data."""
        from app.services import generate_markdown

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.text = (
            "# Generated Markdown\n\n## Content\n\nProcessed successfully"
        )
        mock_client.aio.models.generate_content.return_value = mock_response

        complex_data = ExtractedData(
            text="Multi-paragraph text with special characters: ñáéíóú",
            tables=[
                Table(
                    headers=["Name", "Age", "City"],
                    rows=[
                        ["John Doe", "30", "New York"],
                        ["Jane Smith", "25", "Los Angeles"],
                    ],
                )
            ],
        )

        result = await generate_markdown(complex_data)
        assert result == "# Generated Markdown\n\n## Content\n\nProcessed successfully"
        mock_client.aio.models.generate_content.assert_called_once()

    def test_extracted_data_model_validation(self):
        """Test ExtractedData model validation."""
        # Test valid data
        valid_data = ExtractedData(
            text="Sample text", tables=[Table(headers=["A", "B"], rows=[["1", "2"]])]
        )
        assert valid_data.text == "Sample text"
        assert len(valid_data.tables) == 1

        # Test empty data
        empty_data = ExtractedData()
        assert empty_data.text == ""
        assert empty_data.tables == []

        # Test table validation
        table = Table(headers=["Col1", "Col2"], rows=[["A", "B"], ["C", "D"]])
        assert table.headers == ["Col1", "Col2"]
        assert len(table.rows) == 2


class TestIntegrationScenarios:
    """Integration tests covering complete workflows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.main.redis_client")
    @patch("app.main.process_file")
    @patch("app.main.magic")
    async def test_complete_pdf_workflow(
        self, mock_magic, mock_process_file, mock_redis, client
    ):
        """Test complete PDF processing workflow."""
        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        mock_task = MagicMock()
        task_id = str(uuid4())
        mock_task.id = task_id
        mock_task.status = "SUCCESS"
        mock_task.result = {
            "markdown": "# Test Document\n\nExtracted content here.",
            "tokens": {"input": 100, "output": 50},
        }
        mock_process_file.delay.return_value = mock_task

        # Upload file
        pdf_content = b"%PDF-1.4 test content"
        upload_response = client.post(
            "/uploadfile/", files={"file": ("test.pdf", pdf_content, "application/pdf")}
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["task_id"] == task_id

        # Check task status
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task
            status_response = client.get(f"/api/tasks/{task_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "SUCCESS"

        # Download result
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task
            download_response = client.get(f"/download_markdown/{task_id}")
            assert download_response.status_code == 200
            assert (
                download_response.headers["content-type"] == "application/octet-stream"
            )

    @patch("app.main.redis_client")
    async def test_rate_limiting_scenario(self, mock_redis, client):
        """Test rate limiting functionality."""
        mock_redis.ping = AsyncMock(return_value=True)

        # This would require actual rate limiting to be configured
        # For now, just verify the endpoint responds normally
        response = client.get("/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
