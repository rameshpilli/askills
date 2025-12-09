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

    # API credentials
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

    # Corporate LLM Gateway settings
    # ANTHROPIC_BASE_URL is the standard env var used by Anthropic SDK
    ANTHROPIC_BASE_URL: str = os.environ.get("ANTHROPIC_BASE_URL", "")

    # Alternative name for gateway URL (for backwards compatibility)
    LLM_GATEWAY_URL: str = os.environ.get("LLM_GATEWAY_URL", "")

    # Custom headers for gateway authentication (JSON string)
    # Example: '{"X-Api-Key": "your-key", "X-Tenant-Id": "your-tenant"}'
    LLM_GATEWAY_HEADERS: str = os.environ.get("LLM_GATEWAY_HEADERS", "")

    # Model override (some gateways use different model names)
    CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "")

    @classmethod
    def get_base_url(cls) -> str:
        """Get the API base URL (gateway or default Anthropic)."""
        return cls.ANTHROPIC_BASE_URL or cls.LLM_GATEWAY_URL or ""

    @classmethod
    def get_gateway_headers(cls) -> dict:
        """Parse gateway headers from JSON string."""
        if cls.LLM_GATEWAY_HEADERS:
            import json
            try:
                return json.loads(cls.LLM_GATEWAY_HEADERS)
            except json.JSONDecodeError:
                return {}
        return {}

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
        return bool(cls.ANTHROPIC_API_KEY or cls.get_base_url())

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
