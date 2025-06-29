Use venv from .venv or venv.
Don't launch the app with the default port. Use the port from the config.
Run `ruff check` after every change to python files.
Instead of os module use pathlib.
Use uv for package management
Adhere to DRY and KISS principles
Use modern practices
The code should be concise but readable.
Always use `start.sh` to launch the application and its services after any changes. This script will automatically kill any existing processes and restart them.
Always update GEMINI.md with made changes. For the future developers.
Always add new packages to pyproject.toml
Always add required apps to the dockerfile's installation block, and ensure Celery worker is started in post-create.sh

### UI Enhancements (2025-06-28)

- Added a bounce animation to the "Tasks" button when a new file is uploaded, indicating a new task.
- Implemented counters on the "Tasks" button to display the number of pending and completed tasks.
- Enhanced the file upload area to support both drag-and-drop and click-to-select functionalities, improving user interaction for file uploads.
- Integrated Tailwind CSS into the project's build process. To compile Tailwind CSS, run `npm run build:tailwind`.
- Removed custom CSS from `app/static/input.css` to rely solely on Tailwind CSS for styling.
- Applied inline styles to SVG elements in `app/templates/index.html` to ensure correct icon sizing.
- Reverted `app/static/input.css` to only contain `@tailwind` directives.
