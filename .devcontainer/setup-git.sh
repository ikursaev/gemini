#!/bin/bash

# This script can be run before starting the devcontainer to copy Git configuration
# Run this from your host machine to prepare Git config for the container

echo "Preparing Git configuration for devcontainer..."

# Create temporary directory for sharing config
mkdir -p /tmp/devcontainer-git

# Copy Git config if it exists
if [ -f "$HOME/.gitconfig" ]; then
    cp "$HOME/.gitconfig" /tmp/devcontainer-git/.gitconfig-host
    echo "✅ Git config copied"
else
    echo "⚠️  No Git config found at $HOME/.gitconfig"
fi

# Copy SSH keys if they exist
if [ -d "$HOME/.ssh" ]; then
    cp -r "$HOME/.ssh" /tmp/devcontainer-git/.ssh-host
    echo "✅ SSH keys copied"
else
    echo "⚠️  No SSH directory found at $HOME/.ssh"
fi

echo "Git configuration prepared for devcontainer"
echo "You can now start the devcontainer"
