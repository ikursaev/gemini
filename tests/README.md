# Document Extractor Test Suite

This directory contains a comprehensive test suite for the Document Extractor application.

## Test Structure

### Core Test Files

- **`test_app.py`** - Original test suite covering basic functionality
- **`test_advanced.py`** - Advanced tests for edge cases, error handling, and complex scenarios
- **`test_performance.py`** - Performance and load testing
- **`test_edge_cases.py`** - Edge cases and error scenario testing
- **`test_integration.py`** - End-to-end integration tests
- **`conftest.py`** - Test configuration, fixtures, and utilities

### Test Categories

#### Unit Tests

- Configuration validation
- Utility function testing
- Individual component testing
- Error handling validation

#### Integration Tests

- Complete workflow testing (upload → process → download)
- API endpoint integration
- Redis integration
- Task processing pipeline

#### Performance Tests

- Response time benchmarks
- Concurrent request handling
- Memory usage monitoring
- Load testing scenarios

#### Edge Case Tests

- File corruption handling
- Network failure simulation
- Resource exhaustion scenarios
- Data validation edge cases

## Running Tests

### Prerequisites

Install test dependencies:

```bash
uv add --dev pytest pytest-asyncio pytest-cov pytest-html httpx pillow psutil
```

### Basic Test Execution

Run all tests:

```bash
python run_tests.py
```

Run with verbose output:

```bash
python run_tests.py --verbose
```

### Specific Test Categories

Run only fast tests (skip performance tests):

```bash
python run_tests.py --fast
```

Run only performance tests:

```bash
python run_tests.py --performance
```

### Coverage Reports

Generate coverage report:

```bash
python run_tests.py --coverage
```

Generate HTML coverage report:

```bash
python run_tests.py --coverage --html
```

### Direct pytest Usage

You can also run pytest directly:

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_integration.py -v

# Tests by marker
pytest tests/ -m "not performance" -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Fixtures and Utilities

### Common Fixtures

- **`test_client`** - FastAPI test client
- **`mock_redis`** - Mock Redis client with common methods
- **`mock_celery_task`** - Mock Celery task
- **`sample_pdf_bytes`** - Sample PDF content for testing
- **`sample_image_bytes`** - Sample image content for testing
- **`temp_file`** - Temporary file creation and cleanup

### Mock Factories

- **`TestDataFactory`** - Creates test data objects
- **`MockExtractedData`** - Mock extracted document data
- **`MockTable`** - Mock table data structures

### Assertion Helpers

- **`TestAssertions.assert_valid_task_response()`** - Validates task response structure
- **`TestAssertions.assert_valid_task_status()`** - Validates task status structure
- **`TestAssertions.assert_valid_health_response()`** - Validates health check response

### Performance Utilities

- **`PerformanceTimer`** - Context manager for measuring execution time
- Memory usage monitoring
- Concurrent execution helpers

## Test Configuration

### Environment Variables

Tests use a separate configuration:

- `REDIS_DB=1` (different from production DB 0)
- `MAX_FILE_SIZE=10MB` (smaller limit for testing)
- Test-specific API keys and settings

### Markers

- **`@pytest.mark.performance`** - Performance tests
- **`@pytest.mark.integration`** - Integration tests
- **`@pytest.mark.slow`** - Slow-running tests

## Mocking Strategy

### External Dependencies

All external dependencies are mocked:

- **Redis** - Mock async Redis client
- **Google Gemini API** - Mock API responses
- **Celery** - Mock task execution
- **File system** - Temporary files with cleanup

### Mock Patterns

1. **Service Layer Mocking** - Mock service functions with realistic responses
2. **API Client Mocking** - Mock external API calls
3. **Database Mocking** - Mock Redis operations
4. **File Operation Mocking** - Mock file I/O operations

## Coverage Goals

- **Overall Coverage**: >90%
- **Core Business Logic**: >95%
- **Error Handling**: >80%
- **Integration Paths**: >85%

## Test Data

### Sample Files

Tests use various sample files:

- **Valid PDF**: Minimal PDF structure
- **Valid Images**: PNG, JPEG test images
- **Corrupted Files**: Invalid file headers
- **Large Files**: Files at size limits
- **Unicode Filenames**: International character testing

### Expected Responses

Mock responses match production API structures:

- Task creation responses
- Status check responses
- Error message formats
- Health check responses

## Continuous Integration

### GitHub Actions

Tests run automatically on:

- Pull requests
- Pushes to main branch
- Scheduled runs (daily)

### Test Reports

- Coverage reports uploaded to Codecov
- HTML test reports generated
- Performance benchmarks tracked

## Debugging Tests

### Verbose Output

Use `-v` flag for detailed test output:

```bash
pytest tests/ -v -s
```

### Specific Test Debugging

Run single test with full output:

```bash
pytest tests/test_integration.py::TestCompleteWorkflows::test_pdf_complete_workflow -v -s
```

### Test Coverage Analysis

Generate detailed coverage report:

```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

## Performance Benchmarks

### Response Time Targets

- Health check: < 100ms
- File upload: < 2s (medium files)
- Task status: < 200ms
- Main page load: < 500ms

### Concurrency Targets

- 10 concurrent health checks: < 2s total
- 5 concurrent uploads: < 5s total
- No memory leaks during load testing

### Resource Limits

- Memory increase during testing: < 50MB
- No file handle leaks
- Proper cleanup of temporary files

## Adding New Tests

### Test File Organization

1. **Unit tests** → Add to appropriate existing file
2. **New feature tests** → Create new test file
3. **Performance tests** → Add to `test_performance.py`
4. **Integration tests** → Add to `test_integration.py`

### Test Naming Convention

- Test classes: `TestFeatureName`
- Test methods: `test_specific_scenario`
- Fixtures: `fixture_name` (descriptive)

### Mock Guidelines

1. Mock external dependencies
2. Use realistic response data
3. Include error scenarios
4. Clean up resources in fixtures

## Troubleshooting

### Common Issues

1. **Import errors** - Check PYTHONPATH and dependencies
2. **Mock failures** - Verify mock setup matches actual API
3. **Async test issues** - Use `pytest-asyncio` properly
4. **File cleanup** - Ensure fixtures clean up temporary files

### Debug Tips

1. Use `pytest --pdb` for debugging
2. Add `print()` statements in tests (use `-s` flag)
3. Check mock call counts and arguments
4. Verify fixture setup and teardown
