Use venv from .venv or venv.
Don't launch the app with the default port. Use the port from the config.
Run `ruff check` after every change to python files.
Instead of os module use pathlib.
Use uv for package management
Adhere to DRY and KISS principles
Use modern practices
The code should be concise but readable.
Launch the app after each change. Use browser to check that it loads up. Use the browser to also check what's on the page when logs change.
Always update GEMINI.md with made changes. For the future developers.
Always add new packages to pyproject.toml
Always add required apps to the dockerfile's installation block, and ensure Celery worker is started in post-create.sh

### UI Enhancements (2025-06-28)

- Added a bounce animation to the "Tasks" button when a new file is uploaded, indicating a new task.
- Implemented counters on the "Tasks" button to display the number of pending and completed tasks.
