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

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

RUN uv venv

# Set up npm global package folder
RUN mkdir -p /usr/local/share/npm-global \
  && chown -R node:node /usr/local/share/npm-global

# Switch to node user
USER node

# Set up npm configuration
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Set up workspace
WORKDIR /workspace

# Configure git to be safe with the workspace directory
RUN git config --global --add safe.directory /workspace

# Set up shell environment
RUN echo 'source /etc/bash_completion' >> ~/.bashrc \
  && echo 'alias ll="ls -la"' >> ~/.bashrc \
  && echo 'alias la="ls -A"' >> ~/.bashrc \
  && echo 'alias l="ls -CF"' >> ~/.bashrc

# Default command
CMD ["bash"]
