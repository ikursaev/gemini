"""Test configuration and fixtures for the Document Extractor test suite.

This module provides:
- Common test fixtures
- Test configuration
- Mock factories
- Test utilities
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture(scope="session")
def test_settings():
    """Test settings override."""
    # Override settings for testing
    test_settings = {
        "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB for tests
        "REDIS_HOST": "localhost",
        "REDIS_PORT": 6379,
        "REDIS_DB": 1,  # Use different DB for tests
    }
    return test_settings


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client with common methods."""
    mock = MagicMock()
    mock.ping = AsyncMock(return_value=True)
    mock.lpush = AsyncMock()
    mock.expire = AsyncMock()
    mock.lrange = AsyncMock(return_value=[])
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_celery_task():
    """Mock Celery task."""
    task = MagicMock()
    task.id = "test-task-id"
    task.status = "PENDING"
    task.result = None
    return task


@pytest.fixture
def sample_pdf_bytes():
    """Sample PDF file content for testing."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n175\n%%EOF"


@pytest.fixture
def sample_image_bytes():
    """Sample image file content for testing."""
    # Create a small test image
    image = Image.new("RGB", (100, 100), color="red")
    import io

    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG")
    return img_buffer.getvalue()


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_path = Path(tmp.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_pdf_file(sample_pdf_bytes):
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(sample_pdf_bytes)
        temp_path = Path(tmp.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_image_file(sample_image_bytes):
    """Create a temporary image file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(sample_image_bytes)
        temp_path = Path(tmp.name)
    yield temp_path
    temp_path.unlink(missing_ok=True)


class MockExtractedData:
    """Mock extracted data for testing."""

    def __init__(self, text="Sample text", tables=None):
        self.text = text
        self.tables = tables or []


class MockTable:
    """Mock table data for testing."""

    def __init__(self, headers=None, rows=None):
        self.headers = headers or ["Col1", "Col2"]
        self.rows = rows or [["A", "B"], ["C", "D"]]


@pytest.fixture
def mock_extracted_data():
    """Mock extracted data with sample content."""
    return MockExtractedData(
        text="This is sample extracted text content.", tables=[MockTable()]
    )


@pytest.fixture
def mock_google_api_client():
    """Mock Google API client."""
    client = MagicMock()

    # Mock file upload
    upload_response = MagicMock()
    upload_response.file.uri = "gs://test-bucket/test-file"
    client.aio.files.upload = AsyncMock(return_value=upload_response)

    # Mock content generation
    generation_response = MagicMock()
    generation_response.text = "# Generated Markdown\n\nSample content"
    client.aio.models.generate_content = AsyncMock(return_value=generation_response)

    # Mock token counting
    token_response = MagicMock()
    token_response.total_tokens = 100
    client.aio.models.count_tokens = AsyncMock(return_value=token_response)

    return client


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "slow" in item.nodeid:
            item.add_marker(pytest.mark.slow)


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_task_metadata(status="PENDING", filename="test.pdf"):
        """Create task metadata for testing."""
        import time

        return {"filename": filename, "timestamp": int(time.time()), "status": status}

    @staticmethod
    def create_file_upload_data(
        filename="test.pdf", content=b"test content", mime_type="application/pdf"
    ):
        """Create file upload data for testing."""
        return {"filename": filename, "content": content, "mime_type": mime_type}

    @staticmethod
    def create_task_result(markdown="# Test", input_tokens=100, output_tokens=50):
        """Create task result data for testing."""
        return {
            "markdown": markdown,
            "tokens": {"input": input_tokens, "output": output_tokens},
        }


# Assertion helpers
class TestAssertions:
    """Custom assertion helpers for tests."""

    @staticmethod
    def assert_valid_task_response(response_data):
        """Assert that task response has valid structure."""
        assert "task_id" in response_data
        assert "filename" in response_data
        assert isinstance(response_data["task_id"], str)
        assert len(response_data["task_id"]) > 0

    @staticmethod
    def assert_valid_task_status(status_data):
        """Assert that task status has valid structure."""
        assert "status" in status_data
        assert status_data["status"] in [
            "PENDING",
            "STARTED",
            "SUCCESS",
            "FAILURE",
            "RETRY",
        ]

    @staticmethod
    def assert_valid_health_response(health_data):
        """Assert that health response has valid structure."""
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "unhealthy"]
        if "redis" in health_data:
            assert health_data["redis"] in ["connected", "disconnected"]


# Performance test utilities
class PerformanceTimer:
    """Utility for measuring test performance."""

    def __init__(self, threshold_ms=1000):
        self.threshold_ms = threshold_ms
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        assert duration_ms < self.threshold_ms, (
            f"Operation took {duration_ms:.1f}ms, expected < {self.threshold_ms}ms"
        )

    @property
    def duration_ms(self):
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None
