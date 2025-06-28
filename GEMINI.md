Use venv. Or create one if there's none.
Don't launch the app with the default port. Use the port from the config.
Run `ruff check` after each change.
Instead of os module use pathlib.
Instead of pip use uv
Launch the app after each change. Use browser to check that it loads up. Use the browser to also check what's on the page when logs change.
Always add description of made changes to this file. For the future developers.
Always add new packages to requirements.txt
Always add required apps to the dockerfile's installation block
