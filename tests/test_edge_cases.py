"""Edge cases and error scenario testing for the Document Extractor application.

This module contains tests for:
- Error handling scenarios
- Edge cases in file processing
- Network failure simulation
- API error responses
- Data corruption scenarios
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestErrorHandling:
    """Error handling and edge case tests."""

    @pytest.fixture
    def client(self):
        """Create test client."""
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

    def test_upload_with_network_timeout(self, client, mock_redis):
        """Test file upload when network timeout occurs."""
        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_process_file.delay.side_effect = TimeoutError("Network timeout")

            test_file_content = b"test pdf content"
            response = client.post(
                "/uploadfile/",
                files={"file": ("test.pdf", test_file_content, "application/pdf")},
            )

            assert response.status_code == 500
            data = response.json()
            assert "Failed to create processing task" in data["detail"]

    def test_upload_with_corrupted_file_header(self, client, mock_redis):
        """Test upload with corrupted file header."""
        with patch("app.main.magic") as mock_magic:
            # Simulate corrupted file detection
            mock_magic.from_file.side_effect = Exception("Corrupted file header")

            response = client.post(
                "/uploadfile/",
                files={"file": ("corrupted.pdf", b"corrupted", "application/pdf")},
            )

            assert response.status_code == 500

    def test_health_check_with_redis_exception(self, client):
        """Test health check when Redis throws unexpected exception."""
        with patch("app.main.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(
                side_effect=ConnectionError("Redis unreachable")
            )

            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["redis"] == "disconnected"

    def test_task_status_with_malformed_task_id(self, client, mock_redis):
        """Test task status with malformed task ID."""
        response = client.get(
            "/api/tasks/malformed-task-id-with-special-chars!@#/status"
        )
        assert response.status_code == 200  # Should handle gracefully

    def test_download_with_task_result_corruption(self, client, mock_redis):
        """Test download when task result is corrupted."""
        with patch("app.main.AsyncResult") as mock_result:
            mock_task = MagicMock()
            mock_task.status = "SUCCESS"
            mock_task.result = {"corrupted": "data", "missing_markdown": True}
            mock_result.return_value = mock_task

            response = client.get("/download_markdown/corrupted-task")
            assert response.status_code == 500

    def test_upload_file_with_unicode_filename(self, client, mock_redis):
        """Test upload with Unicode characters in filename."""
        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_task = MagicMock()
            mock_task.id = "unicode-task"
            mock_process_file.delay.return_value = mock_task

            unicode_filename = "测试文件_тест_📄.pdf"
            test_file_content = b"test content"

            response = client.post(
                "/uploadfile/",
                files={
                    "file": (unicode_filename, test_file_content, "application/pdf")
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == unicode_filename

    def test_upload_file_with_extremely_long_filename(self, client, mock_redis):
        """Test upload with extremely long filename."""
        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_task = MagicMock()
            mock_task.id = "long-name-task"
            mock_process_file.delay.return_value = mock_task

            # Create a filename that's 255+ characters
            long_filename = "a" * 250 + ".pdf"
            test_file_content = b"test content"

            response = client.post(
                "/uploadfile/",
                files={"file": (long_filename, test_file_content, "application/pdf")},
            )

            # Should handle gracefully
            assert response.status_code in [200, 400]

    def test_multiple_files_upload_attempt(self, client, mock_redis):
        """Test uploading multiple files in single request."""
        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_task = MagicMock()
            mock_task.id = "multi-file-task"
            mock_process_file.delay.return_value = mock_task

            # Try to upload multiple files
            response = client.post(
                "/uploadfile/",
                files=[
                    ("file", ("test1.pdf", b"content1", "application/pdf")),
                    ("file", ("test2.pdf", b"content2", "application/pdf")),
                ],
            )

            # Should process only the last file or handle appropriately
            assert response.status_code in [200, 400]


class TestDataValidationEdgeCases:
    """Data validation edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_file_with_null_bytes(self, client):
        """Test file upload with null bytes in content."""
        with (
            patch("app.main.redis_client") as mock_redis,
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lpush = AsyncMock()
            mock_redis.expire = AsyncMock()
            mock_magic.from_file.return_value = "application/pdf"
            mock_task = MagicMock()
            mock_task.id = "null-bytes-task"
            mock_process_file.delay.return_value = mock_task

            # File content with null bytes
            null_byte_content = b"test\x00content\x00with\x00nulls"

            response = client.post(
                "/uploadfile/",
                files={
                    "file": ("null_bytes.pdf", null_byte_content, "application/pdf")
                },
            )

            # Should handle gracefully
            assert response.status_code == 200

    def test_file_with_binary_content(self, client):
        """Test file upload with binary content."""
        with (
            patch("app.main.redis_client") as mock_redis,
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lpush = AsyncMock()
            mock_redis.expire = AsyncMock()
            mock_magic.from_file.return_value = "application/pdf"
            mock_task = MagicMock()
            mock_task.id = "binary-task"
            mock_process_file.delay.return_value = mock_task

            # Random binary content
            binary_content = bytes(range(256))

            response = client.post(
                "/uploadfile/",
                files={"file": ("binary.pdf", binary_content, "application/pdf")},
            )

            assert response.status_code == 200

    def test_mime_type_spoofing_attempt(self, client):
        """Test file upload with mismatched MIME type and content."""
        with (
            patch("app.main.redis_client") as mock_redis,
            patch("app.main.magic") as mock_magic,
        ):
            mock_redis.ping = AsyncMock(return_value=True)
            # Magic detects actual type different from claimed type
            mock_magic.from_file.return_value = "text/plain"

            # Claim it's a PDF but upload text
            text_content = b"This is actually a text file"

            response = client.post(
                "/uploadfile/",
                files={"file": ("fake.pdf", text_content, "application/pdf")},
            )

            # Should reject based on actual content type
            assert response.status_code == 400
            data = response.json()
            assert "Unsupported file type" in data["detail"]


class TestConcurrencyEdgeCases:
    """Concurrency and race condition tests."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_simultaneous_task_status_checks(self, client):
        """Test simultaneous task status checks for same task."""
        from concurrent.futures import ThreadPoolExecutor

        with (
            patch("app.main.redis_client") as mock_redis,
            patch("app.main.AsyncResult") as mock_result,
        ):
            mock_redis.ping = AsyncMock(return_value=True)
            mock_task = MagicMock()
            mock_task.status = "SUCCESS"
            mock_task.result = {
                "markdown": "# Test",
                "tokens": {"input": 100, "output": 50},
            }
            mock_result.return_value = mock_task

            results = []

            def check_status():
                response = client.get("/api/tasks/same-task/status")
                results.append(response.status_code)

            # 10 simultaneous requests for same task
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(check_status) for _ in range(10)]
                for future in futures:
                    future.result()

            # All should succeed
            assert all(status == 200 for status in results)
            assert len(results) == 10

    def test_rapid_upload_different_files(self, client):
        """Test rapid uploads of different files."""
        with (
            patch("app.main.redis_client") as mock_redis,
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lpush = AsyncMock()
            mock_redis.expire = AsyncMock()
            mock_magic.from_file.return_value = "application/pdf"

            # Mock different task IDs for each upload
            task_counter = 0

            def mock_delay(*args, **kwargs):
                nonlocal task_counter
                task_counter += 1
                mock_task = MagicMock()
                mock_task.id = f"rapid-task-{task_counter}"
                return mock_task

            mock_process_file.delay.side_effect = mock_delay

            # Rapid sequential uploads
            responses = []
            for i in range(5):
                file_content = f"content for file {i}".encode()
                response = client.post(
                    "/uploadfile/",
                    files={"file": (f"rapid{i}.pdf", file_content, "application/pdf")},
                )
                responses.append(response.status_code)

            # All should succeed
            assert all(status == 200 for status in responses)


class TestResourceExhaustionScenarios:
    """Resource exhaustion and limit testing."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_max_filename_length_handling(self, client):
        """Test handling of maximum filename length."""
        with (
            patch("app.main.redis_client") as mock_redis,
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
        ):
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lpush = AsyncMock()
            mock_redis.expire = AsyncMock()
            mock_magic.from_file.return_value = "application/pdf"
            mock_task = MagicMock()
            mock_task.id = "max-filename-task"
            mock_process_file.delay.return_value = mock_task

            # Filename at filesystem limit (usually 255 chars)
            max_filename = "a" * 251 + ".pdf"  # 255 chars total
            test_content = b"test content"

            response = client.post(
                "/uploadfile/",
                files={"file": (max_filename, test_content, "application/pdf")},
            )

            # Should handle gracefully
            assert response.status_code in [200, 400]

    def test_task_list_with_corrupted_metadata(self, client):
        """Test task list endpoint with corrupted task metadata."""
        with patch("app.main.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lrange = AsyncMock(return_value=["task1", "task2", "task3"])

            # Mock corrupted metadata
            async def mock_get(key):
                if "task1" in key:
                    return '{"corrupted": "json"}'  # Missing required fields
                elif "task2" in key:
                    return "invalid json content"  # Invalid JSON
                elif "task3" in key:
                    return None  # Missing metadata
                return None

            mock_redis.get = AsyncMock(side_effect=mock_get)

            response = client.get("/api/tasks")
            assert response.status_code == 200
            data = response.json()
            # Should filter out corrupted entries gracefully
            assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
