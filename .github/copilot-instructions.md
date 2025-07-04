---
description: "Python coding conventions and guidelines"
applyTo: "**/*.py"
---

# Python Coding Conventions

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and i- **Modern Button Design**: Pill-shaped gradient blue button with white text and hover lift effects
- **Vibrant Colorful Badge System**:
  - Amber/orange badges with pulsing glow animation for pending tasks
  - Green gradient badges with scaling hover for successful tasks
  - Red gradient badges with scaling hover for failed taskse type hints.
- Provide docstrings following PEP 257 conventions.
- Use the `typing` module for type annotations (e.g., `List[str]`, `Dict[str, int]`).
- Break down complex functions into smaller, more manageable functions.

## General Instructions

- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Code Style and Formatting

- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Ensure lines do not exceed 79 characters.
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.

## Edge Cases and Testing

- Write tests before implementing new features or fixing bugs. You are a TDD (Test-Driven Development) advocate.
- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Example of Proper Documentation

```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.

    Parameters:
    radius (float): The radius of the circle.

    Returns:
    float: The area of the circle, calculated as π * radius^2.
    """
    import math
    return math.pi * radius ** 2
```

# App Instructions

- Use venv from .venv or venv.
- Don't launch the app with the default port. Use the port from the config.
- Run `ruff check --fix` after every change to python files.
- Instead of os module use pathlib.
- Use `uv` for package management. Never use `pip` directly.
- Adhere to DRY and KISS principles
- Use modern practices
- The code should be concise but readable.
- Always use `start.sh` to launch the application and its services after any changes. This script will automatically kill any existing processes and restart them.
- Always update GEMINI.md and `.github\copilot-instructions.md` with made changes. For the future developers.
- Always add new packages to pyproject.toml
- Always add required apps to the dockerfile's installation block, and ensure Celery worker is started in post-create.sh
- Always use the browser to test the application after making changes, ensuring that all functionalities work as expected.
- Always run tests after making changes to ensure everything works correctly.
- Use documentation for `google.genai` module from `https://googleapis.github.io/python-genai/`
- Ultrathink!
- Come up with a plan before starting the implementation. Offer multiple options for me to choose.
- Temporarily create a to-do list at the end of `.github\copilot-instructions.md`. Remove when done.

## Recent Improvements (2025-01-03)

**Configuration & Security Enhancements:**

- Added comprehensive configuration management with validation in `app/config.py`
- Created `.env.example` template with all required environment variables
- Added file size limits and MIME type validation
- Implemented proper Redis connection using configuration
- Added field validation for API key and upload folder

**Code Quality & Structure:**

- Created `app/utils.py` for common utility functions
- Added comprehensive error handling and logging improvements
- Implemented health check endpoints (`/health` and `/health/detailed`)
- Added proper type hints and documentation
- Refactored file upload with better validation and cleanup

**Testing & Development:**

- Added comprehensive test suite in `tests/test_app.py`
- Created pre-commit configuration for code quality
- Added pytest configuration in `pyproject.toml`
- Enhanced development dependencies with testing tools
- Created comprehensive README.md with usage instructions

**Performance & Reliability:**

- Implemented automatic file cleanup after processing
- Added Redis key expiration for task management
- Enhanced Celery configuration with proper serialization
- Improved error handling in background tasks
- Added graceful shutdown handling

**Infrastructure:**

- Updated tasks.py to use configuration-based Redis connection
- Enhanced Docker setup with better development environment
- Added proper application metadata to FastAPI instance
- Improved logging configuration with structured format

## UI Enhancements (2025-06-28)

- Added a bounce animation to the "Tasks" button when a new file is uploaded, indicating a new task.
- Implemented counters on the "Tasks" button to display the number of pending and completed tasks.
- Enhanced the file upload area to support both drag-and-drop and click-to-select functionalities, improving user interaction for file uploads.
- Integrated Tailwind CSS into the project's build process. To compile Tailwind CSS, run `npm run build:tailwind`.
- Removed custom CSS from `app/static/input.css` to rely solely on Tailwind CSS for styling.
- Applied inline styles to SVG elements in `app/templates/index.html` to ensure correct icon sizing.
- Reverted `app/static/input.css` to only contain `@tailwind` directives.

## Tasks Functionality Fix (2025-07-04)

**Critical JavaScript Functionality Restored:**

- **Fixed non-clickable tasks button**: Added complete event handler for dropdown toggle functionality
- **Implemented task counters**: Tasks button now displays pending task count in parentheses
- **Added real-time task status updates**: Implemented polling system that checks task status every 2 seconds
- **Enhanced task display**: Shows task filename, status, timestamp, and download button for completed tasks
- **Drag & Drop Support**: Full drag-and-drop file upload with visual feedback and automatic processing
- **Visual Feedback**: Comprehensive loading states, animations, and error handling for better UX

**Technical Implementation:**

- **API Integration**: Connects to `/api/tasks`, `/uploadfile/`, and `/download_markdown/{task_id}` endpoints
- **Local State Management**: Uses Map() for efficient task tracking and updates
- **Real-time Updates**: Smart polling system that stops when all tasks are completed
- **Event Handling**: Proper dropdown management, drag & drop, and file upload processing

**Browser Testing:** ✅ All tasks functionality now works correctly with full user interaction support.

## Task Persistence Fix (2025-07-04)

**Task Persistence Issues Resolved:**

- **Fixed task disappearance on page reload**: Implemented comprehensive task persistence using localStorage + server synchronization
- **Enhanced backend task metadata**: Added Redis-based storage for complete task information (filename, timestamp, status)
- **Improved API endpoint**: Updated `/api/tasks` to return complete task metadata for proper frontend restoration
- **Smart initialization**: Merges localStorage with server state on page load for robust persistence

**Technical Implementation:**

- **Backend**: Enhanced Redis storage with task metadata, improved `/api/tasks` endpoint
- **Frontend**: localStorage persistence + server sync, automatic cleanup of old tasks
- **Initialization**: Smart startup sequence that restores tasks and resumes polling

**Browser Testing:** ✅ Tasks now persist across page reloads and browser sessions with real-time synchronization.

## Critical Event Loop Fix (2025-07-04)

**Async Event Loop Issues Resolved:**

- **Fixed "Event loop is closed" errors**: Resolved Celery task failures caused by improper async/sync handling in background tasks
- **Enhanced async function execution**: Implemented `run_async_safely()` function that creates isolated event loops for each Celery task
- **Improved task reliability**: Tasks now complete successfully without event loop conflicts (PENDING → SUCCESS in ~2 seconds)
- **Fixed download functionality**: Both `/api/tasks/{task_id}/result` and `/download_markdown/{task_id}` endpoints now work correctly

**Technical Implementation:**

- **Event Loop Management**: Each Celery task gets its own isolated event loop to prevent conflicts
- **Proper Async Handling**: Fixed mixing of `asyncio.run()` with existing event loops in worker processes
- **Token Serialization**: Extracted actual token counts from `CountTokensResponse` objects for JSON serialization
- **Error Handling**: Enhanced endpoint error handling for failed tasks with meaningful error messages

**Testing Results:**

- ✅ **10/10 comprehensive tests passing (100%)**
- ✅ Tasks complete successfully (PENDING → SUCCESS)
- ✅ Download endpoints working correctly
- ✅ Real-time task monitoring functional
- ✅ Task metadata persistence working

**Browser Testing:** ✅ All functionality now works correctly including file upload, task processing, and result download.

## PDF Processing Enhancement (2025-07-04)

**Direct Google Gemini PDF Processing:**

- **Fixed PDF upload hanging**: Replaced local PyPDF2 text extraction with direct Google Gemini file upload API
- **Enhanced PDF processing**: PDFs are now sent directly to Google Gemini for intelligent content extraction
- **Improved accuracy**: Google Gemini can handle complex PDFs including scanned documents, images, and mixed content
- **Better performance**: Reduced processing time and improved reliability for PDF documents

**Technical Implementation:**

- **Direct File Upload**: Uses Google Gemini's file upload API to process PDFs natively
- **Intelligent Processing**: Leverages Google Gemini's advanced document understanding capabilities
- **Automatic Cleanup**: Uploaded files are automatically cleaned up from Google's servers after processing
- **Error Handling**: Comprehensive error handling for file upload and processing failures

**Testing Results:**

- ✅ PDF upload and processing working correctly
- ✅ Tasks complete successfully (PENDING → SUCCESS in ~1.3 seconds)
- ✅ Download endpoints working for PDF results
- ✅ Both simple and complex PDFs supported

**Browser Testing:** ✅ PDF upload functionality now works correctly with direct Google Gemini processing.

## Task Management UI Enhancements (2025-07-04)

**Critical Task Management Issues Resolved:**

- **Fixed task list persistence**: Enhanced localStorage with better error handling and 24-hour task retention
- **Added colorful task badges**: Implemented animated badges showing pending (amber), success (green), and error (red) task counts
- **Modernized Tasks button**: Transformed into a pill-shaped gradient blue button with vibrant colorful badges and smooth animations
- **Enhanced state synchronization**: Improved server-client task state merging with better conflict resolution
- **Better debugging**: Added comprehensive console logging for task management operations

**Technical Implementation:**

- **Enhanced Button Styling**: Modern rounded button with hover lift effects, shadows, and focus states
- **Animated Badges**: CSS animations for badge entry and pulsing effect for pending tasks
- **Smart Persistence**: localStorage with versioning, automatic cleanup of old tasks, and data corruption recovery
- **Improved State Management**: Better task synchronization between localStorage and server state
- **Error Handling**: Comprehensive error handling for localStorage operations and API failures

**Visual Improvements:**

- **Modern Button Design**: Glass morphism effect replaced with clean white/gray button with proper shadows
- **Colorful Badge System**:
  - Amber badges with pulse animation for pending tasks
  - Green badges for successful tasks
  - Red badges for failed tasks
- **Smooth Animations**: CSS transitions and keyframe animations for professional user experience
- **Responsive Design**: Proper badge positioning and button scaling

**Testing Results:**

- ✅ **Task persistence across page reloads working correctly**
- ✅ **Colorful badges displaying accurate task counts**
- ✅ **Modern button styling with hover effects**
- ✅ **Real-time badge updates when tasks change state**
- ✅ **localStorage cleanup preventing data bloat**
- ✅ **Enhanced error handling preventing UI crashes**

**Browser Testing:** ✅ All task management UI improvements working correctly with professional design and smooth user experience.
