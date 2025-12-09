"""
Configuration module for Claude Agent SDK HTTP Service.

Loads configuration from environment variables and .env file.
All configuration values should be accessed through this module.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# First try current directory, then parent directory
load_dotenv()

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """Application configuration loaded from environment variables."""

    # Required
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

    # Optional: Custom LLM gateway URL (for internal deployments)
    LLM_GATEWAY_URL: str = os.environ.get("LLM_GATEWAY_URL", "")

    # Agent settings
    CLAUDE_AGENT_CWD: str = os.environ.get("CLAUDE_AGENT_CWD", "/app")
    CLAUDE_AGENT_SKILLS_DIR: str = os.environ.get("CLAUDE_AGENT_SKILLS_DIR", "/app/skills")

    # Server settings
    HOST: str = os.environ.get("HOST", "0.0.0.0")
    PORT: int = int(os.environ.get("PORT", "8080"))

    # Agent tools configuration
    ALLOWED_TOOLS: list[str] = [
        "Skill",
        "Read",
        "Write",
        "Bash",
        "Edit",
        "Glob",
        "Grep",
    ]

    # Permission mode for the agent
    PERMISSION_MODE: str = "acceptEdits"

    # Setting sources for the agent
    SETTING_SOURCES: list[str] = ["user", "project"]

    @classmethod
    def has_api_credentials(cls) -> bool:
        """Check if API credentials are configured."""
        return bool(cls.ANTHROPIC_API_KEY or cls.LLM_GATEWAY_URL)

    @classmethod
    def get_claude_dir(cls) -> Path:
        """Get the .claude directory path."""
        return Path(cls.CLAUDE_AGENT_CWD) / ".claude"

    @classmethod
    def get_skills_source_path(cls) -> Path:
        """Get the skills source directory path."""
        return Path(cls.CLAUDE_AGENT_SKILLS_DIR)

    @classmethod
    def get_claude_skills_dir(cls) -> Path:
        """Get the .claude/skills directory path."""
        return cls.get_claude_dir() / "skills"


# Singleton instance for easy import
config = Config()
