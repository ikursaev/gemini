# Gemini Document Extractor

A modern FastAPI application that extracts text and tables from PDFs and images using Google's Gemini AI model.

## Features

- 🚀 **Fast Processing**: Asynchronous file processing with Celery background tasks
- 📄 **PDF Support**: Extract text and tables from PDF documents
- 🖼️ **Image Support**: Process images (JPEG, PNG, GIF, BMP, TIFF)
- 📊 **Table Detection**: Automatically detect and extract tables in markdown format
- 🔄 **Real-time Updates**: WebSocket-like task monitoring
- 🛡️ **Security**: Rate limiting and file validation
- 🎨 **Modern UI**: Clean, responsive interface with Tailwind CSS

## Requirements

- Python 3.11+
- Redis server
- Google Gemini API key
- Node.js (for Tailwind CSS compilation)

## Installation

### Using UV (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd gemini

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Install Node.js dependencies
npm install
```

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd gemini

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Node.js dependencies
npm install
```

## Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   PORT=8000
   REDIS_HOST=localhost
   REDIS_PORT=6379
   MAX_FILE_SIZE=10485760  # 10MB
   ```

3. Start Redis server:
   ```bash
   redis-server
   ```

## Usage

### Development

Start the development server:

```bash
# Build Tailwind CSS
npm run build:tailwind

# Start all services (recommended)
bash start.sh
```

Or start services individually:

```bash
# Start Celery worker
celery -A app.tasks worker --loglevel=info

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production

For production deployment, consider:

1. Use a process manager like Supervisor or systemd
2. Configure Redis with persistence
3. Set up proper logging
4. Use a reverse proxy (nginx)
5. Enable HTTPS

## API Endpoints

### Core Endpoints

- `POST /uploadfile/` - Upload a file for processing
- `GET /api/tasks` - Get all task statuses
- `GET /api/tasks/{task_id}/result` - Get task result
- `POST /tasks/{task_id}/stop` - Stop a running task
- `GET /download_markdown/{task_id}` - Download result as markdown

### Health Checks

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health check with component status

### Example Usage

```bash
# Upload a file
curl -X POST "http://localhost:8000/uploadfile/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf"

# Check task status
curl -X GET "http://localhost:8000/api/tasks/{task_id}/result"

# Download result
curl -X GET "http://localhost:8000/download_markdown/{task_id}" \
     -o extracted_content.md
```

## Development

### Code Quality

This project uses several tools to maintain code quality:

- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking
- **Pre-commit**: Git hooks for automated checks
- **Pytest**: Testing framework

### Setup Development Environment

```bash
# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
mypy app/

# Run linting
ruff check
ruff format
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_app.py

# Run tests with verbose output
pytest -v
```

### Project Structure

```
gemini/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── config.py        # Configuration management
│   ├── services.py      # AI processing services
│   ├── tasks.py         # Celery background tasks
│   ├── utils.py         # Utility functions
│   ├── static/          # Static files (CSS, JS)
│   └── templates/       # HTML templates
├── tests/
│   ├── __init__.py
│   └── test_app.py      # Test suite
├── .devcontainer/       # VS Code dev container config
├── .env.example         # Environment template
├── .pre-commit-config.yaml
├── pyproject.toml       # Python project configuration
├── package.json         # Node.js dependencies
├── tailwind.config.js   # Tailwind CSS configuration
└── start.sh            # Development server script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write tests for new features
- Update documentation
- Use pathlib instead of os.path
- Follow DRY and KISS principles

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Ensure Redis server is running
   - Check Redis configuration in .env

2. **API Key Error**
   - Verify your Google Gemini API key
   - Check API key has proper permissions

3. **File Upload Issues**
   - Check file size limits
   - Verify supported file types
   - Ensure upload folder permissions

4. **Celery Worker Issues**
   - Restart Celery worker
   - Check Redis connection
   - Verify task queue status

### Logs

Check application logs for detailed error information:

```bash
# Application logs
tail -f app/app.log

# Celery worker logs
tail -f celery_worker.log

# Uvicorn logs
tail -f uvicorn.log
```

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue on GitHub
4. Check the documentation

---

Built with ❤️ using FastAPI, Celery, and Google Gemini AI
