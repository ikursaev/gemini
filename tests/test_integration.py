"""Integration tests for the Document Extractor application.

This module contains end-to-end integration tests that verify
the complete workflow from file upload to result download.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


class TestCompleteWorkflows:
    """End-to-end workflow testing."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_pdf_file(self):
        """Create a sample PDF file."""
        content = b"%PDF-1.4 test content"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            path = Path(tmp.name)
        yield path, content
        path.unlink(missing_ok=True)

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file."""
        image = Image.new("RGB", (100, 100), color="blue")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp, "PNG")
            path = Path(tmp.name)
            content = path.read_bytes()
        yield path, content
        path.unlink(missing_ok=True)

    @patch("app.main.redis_client")
    @patch("app.main.process_file")
    @patch("app.main.magic")
    def test_pdf_complete_workflow(
        self, mock_magic, mock_process_file, mock_redis, client, sample_pdf_file
    ):
        """Test complete PDF processing workflow."""
        pdf_path, pdf_content = sample_pdf_file

        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.lrange = AsyncMock(return_value=["task1"])
        mock_redis.get = AsyncMock(
            return_value=json.dumps(
                {"filename": "test.pdf", "timestamp": 1625097600, "status": "SUCCESS"}
            )
        )

        task_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.status = "SUCCESS"
        mock_task.result = {
            "markdown": "# Test Document\n\nExtracted content from PDF.",
            "tokens": {"input": 150, "output": 75},
        }
        mock_process_file.delay.return_value = mock_task

        # Step 1: Upload file
        upload_response = client.post(
            "/uploadfile/", files={"file": ("test.pdf", pdf_content, "application/pdf")}
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["task_id"] == task_id
        assert upload_data["filename"] == "test.pdf"

        # Step 2: Check task status
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task

            status_response = client.get(f"/api/tasks/{task_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "SUCCESS"
            assert "result" in status_data
            assert (
                status_data["result"]["markdown"]
                == "# Test Document\n\nExtracted content from PDF."
            )

        # Step 3: Get task result
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task

            result_response = client.get(f"/api/tasks/{task_id}/result")
            assert result_response.status_code == 200
            result_data = result_response.json()
            assert (
                result_data["markdown"]
                == "# Test Document\n\nExtracted content from PDF."
            )
            assert result_data["tokens"]["input"] == 150

        # Step 4: Download markdown file
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task

            download_response = client.get(f"/download_markdown/{task_id}")
            assert download_response.status_code == 200
            assert (
                download_response.headers["content-type"] == "application/octet-stream"
            )
            assert (
                "attachment; filename="
                in download_response.headers["content-disposition"]
            )

        # Step 5: List all tasks
        tasks_response = client.get("/api/tasks")
        assert tasks_response.status_code == 200
        tasks_data = tasks_response.json()
        assert len(tasks_data) >= 1

    @patch("app.main.redis_client")
    @patch("app.main.process_file")
    @patch("app.main.magic")
    def test_image_complete_workflow(
        self, mock_magic, mock_process_file, mock_redis, client, sample_image_file
    ):
        """Test complete image processing workflow."""
        image_path, image_content = sample_image_file

        # Setup mocks
        mock_magic.from_file.return_value = "image/png"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        task_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.status = "SUCCESS"
        mock_task.result = {
            "markdown": "# Image Analysis\n\nExtracted text from image.",
            "tokens": {"input": 200, "output": 100},
        }
        mock_process_file.delay.return_value = mock_task

        # Upload image
        upload_response = client.post(
            "/uploadfile/", files={"file": ("test.png", image_content, "image/png")}
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["task_id"] == task_id

        # Check processing completed
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task

            status_response = client.get(f"/api/tasks/{task_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "SUCCESS"

    @patch("app.main.redis_client")
    def test_health_and_system_endpoints(self, mock_redis, client):
        """Test system health and information endpoints."""
        mock_redis.ping = AsyncMock(return_value=True)

        # Basic health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert health_data["redis"] == "connected"

        # Detailed health check
        detailed_response = client.get("/health/detailed")
        assert detailed_response.status_code == 200
        detailed_data = detailed_response.json()
        assert "system_info" in detailed_data
        assert "redis_status" in detailed_data

        # Main page
        main_response = client.get("/")
        assert main_response.status_code == 200
        assert "text/html" in main_response.headers["content-type"]


class TestErrorScenarios:
    """Test error scenarios in complete workflows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.main.redis_client")
    @patch("app.main.process_file")
    @patch("app.main.magic")
    def test_failed_task_workflow(
        self, mock_magic, mock_process_file, mock_redis, client
    ):
        """Test workflow when task processing fails."""
        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        task_id = str(uuid4())
        mock_task = MagicMock()
        mock_task.id = task_id
        mock_task.status = "FAILURE"
        mock_task.result = Exception("Processing failed")
        mock_process_file.delay.return_value = mock_task

        # Upload file
        test_content = b"test content"
        upload_response = client.post(
            "/uploadfile/",
            files={"file": ("test.pdf", test_content, "application/pdf")},
        )

        assert upload_response.status_code == 200

        # Check failed task status
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task

            status_response = client.get(f"/api/tasks/{task_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "FAILURE"

        # Try to download result (should fail)
        with patch("app.main.AsyncResult") as mock_result:
            mock_result.return_value = mock_task

            download_response = client.get(f"/download_markdown/{task_id}")
            assert download_response.status_code == 400

    @patch("app.main.redis_client")
    def test_redis_failure_workflow(self, mock_redis, client):
        """Test workflow when Redis is unavailable."""
        # Redis ping fails
        mock_redis.ping = AsyncMock(side_effect=Exception("Redis down"))

        # Health check should still work but report disconnected
        health_response = client.get("/health")
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["redis"] == "disconnected"

        # File upload should fail gracefully
        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_redis.lpush = AsyncMock(side_effect=Exception("Redis error"))
            mock_task = MagicMock()
            mock_task.id = "test-task"
            mock_process_file.delay.return_value = mock_task

            test_content = b"test content"
            upload_response = client.post(
                "/uploadfile/",
                files={"file": ("test.pdf", test_content, "application/pdf")},
            )

            # Should succeed despite Redis issues (task creation still works)
            assert upload_response.status_code == 200


class TestConcurrentWorkflows:
    """Test concurrent workflow scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.main.redis_client")
    @patch("app.main.process_file")
    @patch("app.main.magic")
    def test_multiple_concurrent_uploads(
        self, mock_magic, mock_process_file, mock_redis, client
    ):
        """Test multiple files uploaded concurrently."""
        from concurrent.futures import ThreadPoolExecutor

        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        def mock_delay(*args, **kwargs):
            mock_task = MagicMock()
            mock_task.id = str(uuid4())
            mock_task.status = "SUCCESS"
            return mock_task

        mock_process_file.delay.side_effect = mock_delay

        def upload_file(file_id):
            content = f"test content {file_id}".encode()
            response = client.post(
                "/uploadfile/",
                files={"file": (f"test{file_id}.pdf", content, "application/pdf")},
            )
            return response.status_code == 200, response.json().get("task_id")

        # Upload 5 files concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(5)]
            results = [future.result() for future in futures]

        # All uploads should succeed
        assert all(success for success, _ in results)

        # All should have unique task IDs
        task_ids = [task_id for _, task_id in results]
        assert len(set(task_ids)) == 5  # All unique

    @patch("app.main.redis_client")
    def test_concurrent_health_checks(self, mock_redis, client):
        """Test concurrent health check requests."""
        from concurrent.futures import ThreadPoolExecutor

        mock_redis.ping = AsyncMock(return_value=True)

        def check_health():
            response = client.get("/health")
            return response.status_code == 200

        # 10 concurrent health checks
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(10)]
            results = [future.result() for future in futures]

        # All should succeed
        assert all(results)


class TestDataIntegrity:
    """Test data integrity throughout workflows."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.main.redis_client")
    @patch("app.main.process_file")
    @patch("app.main.magic")
    def test_large_file_processing(
        self, mock_magic, mock_process_file, mock_redis, client
    ):
        """Test processing of large files within limits."""
        from app.config import settings

        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        mock_task = MagicMock()
        mock_task.id = "large-file-task"
        mock_task.status = "SUCCESS"
        mock_task.result = {
            "markdown": "# Large Document\n\nProcessed successfully.",
            "tokens": {"input": 1000, "output": 500},
        }
        mock_process_file.delay.return_value = mock_task

        # Create large file (but within limits)
        large_content = b"x" * (settings.MAX_FILE_SIZE // 2)  # Half of max size

        upload_response = client.post(
            "/uploadfile/",
            files={"file": ("large.pdf", large_content, "application/pdf")},
        )

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["task_id"] == "large-file-task"

    def test_file_size_limit_enforcement(self, client):
        """Test that file size limits are properly enforced."""
        from app.config import settings

        # File exceeding maximum size
        oversized_content = b"x" * (settings.MAX_FILE_SIZE + 1)

        upload_response = client.post(
            "/uploadfile/",
            files={"file": ("oversized.pdf", oversized_content, "application/pdf")},
        )

        assert upload_response.status_code == 413
        error_data = upload_response.json()
        assert "exceeds maximum" in error_data["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
