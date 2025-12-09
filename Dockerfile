# Dockerfile for Claude Agent SDK with Skills Support
# Base image: Python 3.11 slim for smaller footprint
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install system dependencies
# - git: required for some pip packages and potential skill repos
# - bash: shell for Bash tool execution
# - build-essential: compiler tools for native extensions
# - curl: useful for debugging and health checks
# - poppler-utils: required for pdf2image (PDF skill)
# - libreoffice: required for xlsx recalculation and document conversion
# - zip/unzip: required for pptx/docx skills (OOXML manipulation)
# - libmagic1: file type detection
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    bash \
    build-essential \
    curl \
    poppler-utils \
    libreoffice \
    zip \
    unzip \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy the application code into the container
COPY app/ /app/

# Copy the skills directory into the container
# Skills will be linked to .claude/skills at runtime
COPY skills/ /app/skills/

# Create the .claude directory structure that the SDK expects
# The main.py will populate .claude/skills with symlinks at runtime
RUN mkdir -p /app/.claude/skills

# Environment variables for the Claude Agent SDK
# CLAUDE_AGENT_CWD: Working directory for the agent
# CLAUDE_AGENT_SKILLS_DIR: Source directory for skills (custom var for our setup)
ENV CLAUDE_AGENT_CWD=/app
ENV CLAUDE_AGENT_SKILLS_DIR=/app/skills

# The ANTHROPIC_API_KEY should be passed at runtime via docker run -e
# Do NOT set it here to avoid baking secrets into the image

# Default command: run the main.py entrypoint
CMD ["python", "main.py"]
