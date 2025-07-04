"""Performance and load testing for the Document Extractor application.

This module contains tests for:
- Performance benchmarks
- Load testing scenarios
- Memory usage monitoring
- Concurrent request handling
- File processing speed tests
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestPerformanceBaseline:
    """Performance baseline tests."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_check_response_time(self, client):
        """Test health check response time is under threshold."""
        with patch("app.main.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(return_value=True)

            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time
            assert response_time < 0.1, (
                f"Health check took {response_time:.3f}s, should be < 0.1s"
            )

    def test_main_page_load_time(self, client):
        """Test main page loads within acceptable time."""
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()

        assert response.status_code == 200
        load_time = end_time - start_time
        assert load_time < 0.5, (
            f"Main page load took {load_time:.3f}s, should be < 0.5s"
        )

    @patch("app.main.redis_client")
    def test_concurrent_health_checks(self, mock_redis, client):
        """Test concurrent health check requests."""
        mock_redis.ping = AsyncMock(return_value=True)

        def make_request():
            response = client.get("/health")
            return response.status_code == 200

        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
            end_time = time.time()

        # All requests should succeed
        assert all(results), "Some concurrent requests failed"

        # Total time should be reasonable
        total_time = end_time - start_time
        assert total_time < 2.0, (
            f"Concurrent requests took {total_time:.3f}s, should be < 2.0s"
        )


class TestFileProcessingPerformance:
    """File processing performance tests."""

    @patch("app.main.process_file")
    @patch("app.main.magic")
    @patch("app.main.redis_client")
    def test_small_file_upload_speed(
        self, mock_redis, mock_magic, mock_process_file, client
    ):
        """Test upload speed for small files."""
        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        mock_task = MagicMock()
        mock_task.id = "test-task"
        mock_process_file.delay.return_value = mock_task

        # Small file (1KB)
        small_file_content = b"test content" * 80  # ~1KB

        start_time = time.time()
        response = client.post(
            "/uploadfile/",
            files={"file": ("small.pdf", small_file_content, "application/pdf")},
        )
        end_time = time.time()

        assert response.status_code == 200
        upload_time = end_time - start_time
        assert upload_time < 0.2, (
            f"Small file upload took {upload_time:.3f}s, should be < 0.2s"
        )

    @patch("app.main.process_file")
    @patch("app.main.magic")
    @patch("app.main.redis_client")
    def test_medium_file_upload_speed(
        self, mock_redis, mock_magic, mock_process_file, client
    ):
        """Test upload speed for medium-sized files."""
        # Setup mocks
        mock_magic.from_file.return_value = "application/pdf"
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        mock_task = MagicMock()
        mock_task.id = "test-task"
        mock_process_file.delay.return_value = mock_task

        # Medium file (1MB)
        medium_file_content = b"test content" * 131072  # ~1MB

        start_time = time.time()
        response = client.post(
            "/uploadfile/",
            files={"file": ("medium.pdf", medium_file_content, "application/pdf")},
        )
        end_time = time.time()

        assert response.status_code == 200
        upload_time = end_time - start_time
        assert upload_time < 2.0, (
            f"Medium file upload took {upload_time:.3f}s, should be < 2.0s"
        )


class TestMemoryUsage:
    """Memory usage monitoring tests."""

    def test_file_upload_memory_cleanup(self):
        """Test that file uploads don't cause memory leaks."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        client = TestClient(app)

        # Upload multiple small files
        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
            patch("app.main.redis_client") as mock_redis,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lpush = AsyncMock()
            mock_redis.expire = AsyncMock()

            mock_task = MagicMock()
            mock_task.id = "test-task"
            mock_process_file.delay.return_value = mock_task

            for i in range(10):
                file_content = b"test content" * 1000  # ~12KB each
                response = client.post(
                    "/uploadfile/",
                    files={"file": (f"test{i}.pdf", file_content, "application/pdf")},
                )
                assert response.status_code == 200

        # Check memory usage after uploads
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        max_acceptable_increase = 50 * 1024 * 1024  # 50MB
        assert memory_increase < max_acceptable_increase, (
            f"Memory increased by {memory_increase / (1024 * 1024):.1f}MB, should be < 50MB"
        )


class TestConcurrencyAndLoad:
    """Concurrency and load testing."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("app.main.redis_client")
    def test_concurrent_file_uploads(self, mock_redis, client):
        """Test concurrent file upload handling."""
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()

        def upload_file(file_id):
            with (
                patch("app.main.process_file") as mock_process_file,
                patch("app.main.magic") as mock_magic,
            ):
                mock_magic.from_file.return_value = "application/pdf"
                mock_task = MagicMock()
                mock_task.id = f"task-{file_id}"
                mock_process_file.delay.return_value = mock_task

                file_content = b"test content" * 100
                response = client.post(
                    "/uploadfile/",
                    files={
                        "file": (f"test{file_id}.pdf", file_content, "application/pdf")
                    },
                )
                return response.status_code == 200

        # Test with 5 concurrent uploads
        with ThreadPoolExecutor(max_workers=5) as executor:
            start_time = time.time()
            futures = [executor.submit(upload_file, i) for i in range(5)]
            results = [future.result() for future in futures]
            end_time = time.time()

        # All uploads should succeed
        assert all(results), "Some concurrent uploads failed"

        # Total time should be reasonable
        total_time = end_time - start_time
        assert total_time < 5.0, (
            f"Concurrent uploads took {total_time:.3f}s, should be < 5.0s"
        )

    @patch("app.main.redis_client")
    def test_rapid_sequential_requests(self, mock_redis, client):
        """Test handling of rapid sequential requests."""
        mock_redis.ping = AsyncMock(return_value=True)

        # Make 20 rapid health check requests
        start_time = time.time()
        responses = []
        for _ in range(20):
            response = client.get("/health")
            responses.append(response.status_code)
        end_time = time.time()

        # All requests should succeed
        assert all(status == 200 for status in responses), "Some rapid requests failed"

        # Average response time should be reasonable
        avg_time = (end_time - start_time) / 20
        assert avg_time < 0.1, (
            f"Average response time {avg_time:.3f}s, should be < 0.1s"
        )

    @patch("app.main.AsyncResult")
    @patch("app.main.redis_client")
    def test_concurrent_task_status_checks(self, mock_redis, mock_result, client):
        """Test concurrent task status checking."""
        mock_redis.ping = AsyncMock(return_value=True)

        # Mock task results
        mock_task = MagicMock()
        mock_task.status = "SUCCESS"
        mock_task.result = {
            "markdown": "# Test",
            "tokens": {"input": 100, "output": 50},
        }
        mock_result.return_value = mock_task

        def check_task_status(task_id):
            response = client.get(f"/api/tasks/task-{task_id}/status")
            return response.status_code == 200

        # Test with 10 concurrent status checks
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(check_task_status, i) for i in range(10)]
            results = [future.result() for future in futures]
            end_time = time.time()

        # All checks should succeed
        assert all(results), "Some concurrent status checks failed"

        # Total time should be reasonable
        total_time = end_time - start_time
        assert total_time < 3.0, (
            f"Concurrent status checks took {total_time:.3f}s, should be < 3.0s"
        )


class TestResourceLimits:
    """Resource limits and edge case testing."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_max_file_size_handling(self, client):
        """Test handling of maximum file size uploads."""
        from app.config import settings

        # Create file at exactly the maximum size
        max_size_content = b"x" * settings.MAX_FILE_SIZE

        with (
            patch("app.main.process_file") as mock_process_file,
            patch("app.main.magic") as mock_magic,
            patch("app.main.redis_client") as mock_redis,
        ):
            mock_magic.from_file.return_value = "application/pdf"
            mock_redis.ping = AsyncMock(return_value=True)
            mock_redis.lpush = AsyncMock()
            mock_redis.expire = AsyncMock()

            mock_task = MagicMock()
            mock_task.id = "test-task"
            mock_process_file.delay.return_value = mock_task

            response = client.post(
                "/uploadfile/",
                files={"file": ("max_size.pdf", max_size_content, "application/pdf")},
            )

            # Should succeed at exactly max size
            assert response.status_code == 200

    def test_empty_file_handling_performance(self, client):
        """Test that empty file handling is fast."""
        start_time = time.time()
        response = client.post(
            "/uploadfile/", files={"file": ("empty.pdf", b"", "application/pdf")}
        )
        end_time = time.time()

        # Should fail quickly
        assert response.status_code == 400
        response_time = end_time - start_time
        assert response_time < 0.1, (
            f"Empty file handling took {response_time:.3f}s, should be < 0.1s"
        )

    @patch("app.main.redis_client")
    def test_many_task_list_requests(self, mock_redis, client):
        """Test performance with many task list requests."""
        # Mock a large number of tasks
        task_ids = [f"task-{i}" for i in range(100)]
        mock_redis.lrange = AsyncMock(return_value=task_ids)

        # Mock task metadata for each task
        async def mock_get(key):
            if "task-" in key:
                return '{"filename": "test.pdf", "timestamp": 1625097600, "status": "SUCCESS"}'
            return None

        mock_redis.get = AsyncMock(side_effect=mock_get)

        start_time = time.time()
        response = client.get("/api/tasks")
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 100

        # Should handle large task lists efficiently
        response_time = end_time - start_time
        assert response_time < 1.0, (
            f"Large task list took {response_time:.3f}s, should be < 1.0s"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
