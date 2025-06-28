# Gemini CLI Development Container

This repository includes a complete development container setup for the Google Gemini CLI project, providing a consistent and isolated development environment.

## Quick Start

1. **Prerequisites**:
   - [Visual Studio Code](https://code.visualstudio.com/)
   - [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
   - [Docker](https://www.docker.com/get-started)

2. **Open in Dev Container**:
   - Clone this repository
   - Open in VS Code
   - When prompted, click "Reopen in Container" or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"

3. **Wait for Setup**:
   - The container will build and install dependencies automatically
   - This may take a few minutes on first run

## What's Included

### Development Environment
- **Node.js 20** - Latest LTS version matching project requirements
- **Python 3** - With `uv` for dependency management
- **TypeScript** - Full IntelliSense and debugging support
- **ESLint & Prettier** - Code linting and formatting
- **Git & GitHub CLI** - Version control and GitHub integration
- **Celery Worker** - Automatically started in the background for task processing

### VS Code Extensions
- TypeScript language support
- ESLint integration
- Prettier code formatter
- GitLens for enhanced Git capabilities
- npm IntelliSense
- Node.js debugging support

### Development Tools
- Build tools (Python3, make, g++)
- CLI utilities (jq, ripgrep, curl)
- Process management tools
- Shell enhancements with bash completion

## Configuration

### Environment Variables

Set up your Gemini API key by creating a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your API key
GEMINI_API_KEY=your_api_key_here
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

### Git Configuration

The devcontainer will work without any Git configuration, but you'll need to set up Git inside the container:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Note**: The devcontainer has been simplified to avoid Windows path issues. Git configuration is handled inside the container during the post-create setup.

## Development Workflow

### Building the Project

```bash
# Install Node.js dependencies (done automatically on container start)
npm ci

# Install Python dependencies (done automatically on container start)
uv pip install -r app/requirements.txt

# Build the project
npm run build

# Build and create bundle
npm run bundle
```

### Running the CLI

```bash
# Start in development mode
npm start

# Start with debugging
npm run debug

# Run the bundled version
./bundle/gemini.js
```

### Testing

```bash
# Run all tests
npm test

# Run integration tests
npm run test:e2e

# Run tests with coverage
npm run test:ci
```

### Code Quality

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Type checking
npm run typecheck

# Run all preflight checks
npm run preflight
```

## Debugging

The container includes several debug configurations:

1. **Debug Gemini CLI** - Debug the CLI in development mode
2. **Debug Gemini CLI (Bundle)** - Debug the bundled version
3. **Debug Tests** - Debug unit tests
4. **Debug Integration Tests** - Debug integration tests

Use `F5` or the VS Code debugger panel to start debugging.

## Project Structure

```
├── .devcontainer/          # Dev container configuration
│   ├── devcontainer.json   # Main container config
│   ├── Dockerfile         # Container image definition
│   └── post-create.sh     # Setup script
├── .vscode/               # VS Code settings
│   └── launch.json        # Debug configurations
├── packages/              # Main source code
│   ├── cli/              # CLI package
│   └── core/             # Core package
├── integration-tests/     # Integration tests
└── scripts/              # Build scripts
```

## Troubleshooting

### Container Won't Start
- Ensure Docker is running
- Check Docker has sufficient resources (4GB+ RAM recommended)
- Try rebuilding the container: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container"

### WSL/Podman Mount Issues
If you're using Podman or WSL and getting mount errors like `bind source path does not exist`, try the simple configuration:

1. Rename `.devcontainer/devcontainer.json` to `.devcontainer/devcontainer-full.json`
2. Rename `.devcontainer/devcontainer-simple.json` to `.devcontainer/devcontainer.json`
3. Rebuild the container

The simple configuration uses the base Node.js image without custom mounts that can cause issues on some Windows/WSL/Podman setups.

### Dependencies Issues
- Rebuild the container to get fresh dependencies
- Check Node.js version: `node --version` (should be 20.x)

### API Key Issues
- Verify your `.env` file is in the project root
- Check the API key is valid at [Google AI Studio](https://aistudio.google.com/apikey)
- Restart the container after setting environment variables

### Git Issues
- Ensure your Git credentials are configured
- SSH keys are mounted from your host machine automatically

## Contributing

This development container is configured for contributing to the Gemini CLI project:

1. Fork the repository
2. Open in the dev container
3. Make your changes
4. Run `npm run preflight` to ensure quality
5. Submit a pull request

## Performance Tips

- The container mounts your Git config and SSH keys for seamless integration
- Node modules are installed in the container for better performance
- Source maps are configured for debugging TypeScript
- File watchers exclude `node_modules` and build directories

## Support

For issues with the development container:
- Check the [troubleshooting section](#troubleshooting) above
- Review VS Code Dev Containers [documentation](https://code.visualstudio.com/docs/remote/containers)
- Open an issue in the repository

For Gemini CLI specific issues, refer to the main [README.md](README.md) and [documentation](docs/).
