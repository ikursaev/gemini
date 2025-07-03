"""Tests for the Gemini CLI application."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.utils import format_file_size, validate_file_size, validate_mime_type


class TestConfig:
    """Test configuration settings."""

    def test_config_has_required_fields(self):
        """Test that all required configuration fields are present."""
        assert hasattr(settings, 'GOOGLE_API_KEY')
        assert hasattr(settings, 'PORT')
        assert hasattr(settings, 'HOST')
        assert hasattr(settings, 'REDIS_HOST')
        assert hasattr(settings, 'UPLOAD_FOLDER_NAME')
        assert hasattr(settings, 'MAX_FILE_SIZE')

    def test_redis_url_property(self):
        """Test that Redis URL is properly formatted."""
        expected_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        assert settings.redis_url == expected_url


class TestUtils:
    """Test utility functions."""

    def test_validate_file_size_valid(self):
        """Test file size validation with valid size."""
        is_valid, error = validate_file_size(1024)  # 1KB
        assert is_valid is True
        assert error == ""

    def test_validate_file_size_empty(self):
        """Test file size validation with empty file."""
        is_valid, error = validate_file_size(0)
        assert is_valid is False
        assert "Empty file" in error

    def test_validate_file_size_too_large(self):
        """Test file size validation with file too large."""
        is_valid, error = validate_file_size(settings.MAX_FILE_SIZE + 1)
        assert is_valid is False
        assert "exceeds maximum" in error

    def test_validate_mime_type_pdf(self):
        """Test MIME type validation with PDF."""
        is_valid, error = validate_mime_type("application/pdf")
        assert is_valid is True
        assert error == ""

    def test_validate_mime_type_image(self):
        """Test MIME type validation with image."""
        is_valid, error = validate_mime_type("image/jpeg")
        assert is_valid is True
        assert error == ""

    def test_validate_mime_type_unsupported(self):
        """Test MIME type validation with unsupported type."""
        is_valid, error = validate_mime_type("text/plain")
        assert is_valid is False
        assert "Unsupported file type" in error

    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        assert format_file_size(512) == "512.0 B"

    def test_format_file_size_kb(self):
        """Test file size formatting for KB."""
        assert format_file_size(1536) == "1.5 KB"

    def test_format_file_size_mb(self):
        """Test file size formatting for MB."""
        assert format_file_size(1572864) == "1.5 MB"

    def test_format_file_size_zero(self):
        """Test file size formatting for zero bytes."""
        assert format_file_size(0) == "0 B"


class TestAPIEndpoints:
    """Test API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch('app.main.redis_client') as mock_redis:
            mock_redis.ping = AsyncMock(return_value=True)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_main_page(self, client):
        """Test main page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @patch('app.main.process_file')
    @patch('app.main.magic')
    @patch('app.main.redis_client')
    def test_upload_file_success(self, mock_redis, mock_magic, mock_process_file, client):
        """Test successful file upload."""
        # Mock dependencies
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_task.status = "PENDING"
        mock_process_file.delay.return_value = mock_task

        # Create test file
        test_file_content = b"test pdf content"
        response = client.post(
            "/uploadfile/",
            files={"file": ("test.pdf", test_file_content, "application/pdf")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["filename"] == "test.pdf"

    def test_upload_file_empty(self, client):
        """Test upload with empty file."""
        response = client.post(
            "/uploadfile/",
            files={"file": ("empty.pdf", b"", "application/pdf")}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Empty file" in data["detail"]

    def test_upload_file_too_large(self, client):
        """Test upload with file too large."""
        large_content = b"x" * (settings.MAX_FILE_SIZE + 1)
        response = client.post(
            "/uploadfile/",
            files={"file": ("large.pdf", large_content, "application/pdf")}
        )

        assert response.status_code == 413
        data = response.json()
        assert "exceeds maximum" in data["detail"]

    @patch('app.main.magic')
    def test_upload_file_unsupported_type(self, mock_magic, client):
        """Test upload with unsupported file type."""
        mock_magic.from_file.return_value = "text/plain"

        response = client.post(
            "/uploadfile/",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file type" in data["detail"]


class TestTaskProcessing:
    """Test task processing functionality."""

    @patch('app.tasks.extract_content_from_pdf')
    @patch('app.tasks.generate_markdown')
    async def test_process_pdf_success(self, mock_generate_markdown, mock_extract_pdf):
        """Test successful PDF processing."""
        from app.tasks import process_file

        # Mock successful extraction
        mock_extract_pdf.return_value = ([], 100, 50)
        mock_generate_markdown.return_value = "# Test Content"

        # Create a mock task
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        # Create a test file
        test_file = Path("test.pdf")
        test_file.write_bytes(b"test content")

        try:
            result = await process_file(mock_task, str(test_file), "application/pdf")

            assert "markdown" in result
            assert "error" not in result
            assert result["markdown"] == "# Test Content"

        finally:
            test_file.unlink(missing_ok=True)

    def test_process_file_not_found(self):
        """Test processing non-existent file."""
        from app.tasks import process_file

        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        # Use async_to_sync decorator manually for testing
        import asyncio
        result = asyncio.run(process_file.__wrapped__(mock_task, "nonexistent.pdf", "application/pdf"))

        assert "error" in result
        assert "File not found" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
