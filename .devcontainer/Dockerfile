FROM node:20-slim

# Install system dependencies for development
RUN apt-get update && apt-get install -y --no-install-recommends \
  # Build tools for native modules
  python3 \
  python3-venv \
  python3-dev \
  python3-pip \
  libmagic-dev \
  redis-server \
  make \
  g++ \
  # Development utilities
  git \
  curl \
  wget \
  unzip \
  ca-certificates \
  # CLI tools
  jq \
  bc \
  less \
  man-db \
  dnsutils \
  # Process management
  procps \
  psmisc \
  lsof \
  # Network tools
  socat \
  # Search tools
  ripgrep \
  # File sync
  rsync \
  # Shell enhancements
  bash-completion \
  # GitHub CLI
  gh \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install uv system-wide
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
# Move uv to system location accessible by all users
RUN mv /root/.local/bin/uv /usr/local/bin/uv

# Set up npm global package folder
RUN mkdir -p /usr/local/share/npm-global \
  && chown -R node:node /usr/local/share/npm-global

# Switch to node user
USER node

# Set up npm configuration
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Update npm and install global packages
RUN npm update -g npm 2>/dev/null || echo "npm update failed, continuing..." \
  && npm install -g @google/gemini-cli 2>/dev/null || echo "Gemini CLI installation failed, continuing..."

# Set up workspace
WORKDIR /workspace

# Configure git to be safe with the workspace directory and set up basic git config
RUN git config --global --add safe.directory /workspace \
  && git config --global init.defaultBranch main \
  && git config --global pull.rebase false

# Create SSH directory structure
RUN mkdir -p ~/.ssh && chmod 700 ~/.ssh

# Create Python virtual environment structure
RUN mkdir -p /workspace/.venv

# Create .env.example template
RUN echo "# Gemini API Configuration" > /workspace/.env.example && \
    echo "GEMINI_API_KEY=your_api_key_here" >> /workspace/.env.example && \
    echo "" >> /workspace/.env.example && \
    echo "# Development settings" >> /workspace/.env.example && \
    echo "NODE_ENV=development" >> /workspace/.env.example && \
    echo "DEBUG=1" >> /workspace/.env.example

# Set up shell environment
RUN echo 'source /etc/bash_completion' >> ~/.bashrc \
  && echo 'alias ll="ls -la"' >> ~/.bashrc \
  && echo 'alias la="ls -A"' >> ~/.bashrc \
  && echo 'alias l="ls -CF"' >> ~/.bashrc

# Default command
CMD ["bash"]
