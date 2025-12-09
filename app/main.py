#!/usr/bin/env python3
"""
Claude Agent SDK HTTP Service with Skills Support

This script:
1. Sets up the skills directory structure expected by the Claude Agent SDK
2. Exposes a FastAPI HTTP API for interacting with the agent
3. Supports skills loading from .claude/skills/

Endpoints:
- POST /chat - Send a message to the agent, get a reply
- POST /chat/verbose - Send a message with step-by-step execution logs
- GET /health - Health check endpoint

Skills Wiring:
- At container build time, skills are copied to /app/skills
- At runtime, this script creates symlinks from /app/.claude/skills/* to /app/skills/*
- The Claude Agent SDK loads SKILL.md files from .claude/skills/

Environment Variables:
- ANTHROPIC_API_KEY: API key for Anthropic (required)
- LLM_GATEWAY_URL: Optional custom gateway URL for internal deployments
- CLAUDE_AGENT_CWD: Working directory for the agent (default: /app)
- CLAUDE_AGENT_SKILLS_DIR: Source skills directory (default: /app/skills)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables from .env file
# Looks for .env in current directory, then parent directories
load_dotenv()

# Also try to load from parent directory (when running from app/)
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def setup_skills_directory():
    """
    Set up the .claude/skills directory structure.

    The Claude Agent SDK expects skills to be in .claude/skills/ relative to
    the working directory. This function creates symlinks from the SDK's
    expected location to our skills source directory.

    Directory structure after setup:
        /app/
        ├── .claude/
        │   └── skills/
        │       ├── skill-one -> /app/skills/skill-one
        │       └── skill-two -> /app/skills/skill-two
        └── skills/
            ├── skill-one/
            │   └── SKILL.md
            └── skill-two/
                └── SKILL.md
    """
    cwd = os.environ.get("CLAUDE_AGENT_CWD", "/app")
    skills_source = os.environ.get("CLAUDE_AGENT_SKILLS_DIR", "/app/skills")

    claude_dir = Path(cwd) / ".claude"
    claude_skills_dir = claude_dir / "skills"
    skills_source_path = Path(skills_source)

    # Ensure .claude directory exists
    claude_dir.mkdir(parents=True, exist_ok=True)
    claude_skills_dir.mkdir(parents=True, exist_ok=True)

    print(f"[Setup] Claude directory: {claude_dir}")
    print(f"[Setup] Skills source: {skills_source_path}")

    # Check if skills source directory exists and has content
    if not skills_source_path.exists():
        print(f"[Setup] Skills source directory does not exist: {skills_source_path}")
        print("[Setup] No skills will be loaded. Add skills to the skills/ directory.")
        return

    # Create symlinks for each skill folder
    skill_count = 0
    for skill_folder in skills_source_path.iterdir():
        if skill_folder.is_dir():
            # Check if this looks like a skill (has SKILL.md)
            skill_md = skill_folder / "SKILL.md"
            if skill_md.exists():
                link_path = claude_skills_dir / skill_folder.name

                # Remove existing link/directory if present
                if link_path.is_symlink() or link_path.exists():
                    if link_path.is_symlink():
                        link_path.unlink()
                    else:
                        import shutil
                        shutil.rmtree(link_path)

                # Create symlink
                link_path.symlink_to(skill_folder.resolve())
                print(f"[Setup] Linked skill: {skill_folder.name}")
                skill_count += 1
            else:
                print(f"[Setup] Skipping {skill_folder.name} (no SKILL.md found)")

    if skill_count == 0:
        print("[Setup] No skills found. Add skill folders with SKILL.md to skills/")
    else:
        print(f"[Setup] Loaded {skill_count} skill(s)")


# Pydantic models for API
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class ExecutionStep(BaseModel):
    step: int
    timestamp: str
    type: str  # "text", "tool_use", "tool_result", "thinking"
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[dict] = None


class VerboseChatResponse(BaseModel):
    reply: str
    steps: List[ExecutionStep]
    total_steps: int
    tools_used: List[str]


class HealthResponse(BaseModel):
    status: str
    skills_loaded: int


# FastAPI app
app = FastAPI(
    title="Claude Agent SDK Service",
    description="HTTP API for Claude Agent with Skills support",
    version="1.0.0",
)

# Global agent options (initialized on startup)
agent_options = None
skills_count = 0


def init_agent_options():
    """Initialize Claude Agent options."""
    from claude_agent_sdk import ClaudeAgentOptions

    cwd = os.environ.get("CLAUDE_AGENT_CWD", "/app")

    return ClaudeAgentOptions(
        cwd=cwd,
        # Load settings and skills from both user and project directories
        setting_sources=["user", "project"],
        # Tools available to the agent
        allowed_tools=["Skill", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
        # Accept file edits automatically
        permission_mode="acceptEdits",
    )


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global agent_options, skills_count

    print("=" * 60)
    print("Claude Agent SDK HTTP Service Starting...")
    print("=" * 60)

    # Step 1: Set up skills directory
    print("\n[Step 1] Setting up skills directory...")
    setup_skills_directory()

    # Count skills
    cwd = os.environ.get("CLAUDE_AGENT_CWD", "/app")
    claude_skills_dir = Path(cwd) / ".claude" / "skills"
    if claude_skills_dir.exists():
        skills_count = len([d for d in claude_skills_dir.iterdir() if d.is_dir() or d.is_symlink()])

    # Step 2: Initialize agent options
    print("\n[Step 2] Initializing agent options...")
    try:
        agent_options = init_agent_options()
        print("[Setup] Agent options initialized successfully")
    except ImportError as e:
        print(f"[Error] Failed to import claude_agent_sdk: {e}")
        print("[Error] Make sure claude-agent-sdk is installed")

    print("\n" + "=" * 60)
    print(f"Service ready! Skills loaded: {skills_count}")
    print("=" * 60 + "\n")


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if agent_options else "not_initialized",
        skills_loaded=skills_count,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Send a message to the Claude agent and get a response.

    The agent has access to all configured skills and can use them
    to help answer your questions or perform tasks.
    """
    from claude_agent_sdk import (
        query,
        AssistantMessage,
        TextBlock,
    )

    if not agent_options:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    gateway_url = os.environ.get("LLM_GATEWAY_URL")

    if not api_key and not gateway_url:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY or LLM_GATEWAY_URL environment variable not set"
        )

    # Collect response chunks
    reply_chunks: list[str] = []

    try:
        async for msg in query(prompt=req.message, options=agent_options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        reply_chunks.append(block.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    full_reply = "".join(reply_chunks) if reply_chunks else "No response from agent"

    return ChatResponse(reply=full_reply)


@app.post("/chat/verbose", response_model=VerboseChatResponse)
async def chat_verbose(req: ChatRequest) -> VerboseChatResponse:
    """
    Send a message to the Claude agent with detailed step-by-step execution logs.

    Returns:
    - reply: The final response text
    - steps: Array of execution steps showing model decisions, tool usage, etc.
    - total_steps: Total number of execution steps
    - tools_used: List of tools/skills that were invoked
    """
    from claude_agent_sdk import (
        query,
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
        ThinkingBlock,
    )

    if not agent_options:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    gateway_url = os.environ.get("LLM_GATEWAY_URL")

    if not api_key and not gateway_url:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY or LLM_GATEWAY_URL environment variable not set"
        )

    # Collect response and execution steps
    reply_chunks: list[str] = []
    steps: list[ExecutionStep] = []
    tools_used: list[str] = []
    step_num = 0

    def add_step(step_type: str, content: str, tool_name: str = None, tool_input: dict = None):
        nonlocal step_num
        step_num += 1
        steps.append(ExecutionStep(
            step=step_num,
            timestamp=datetime.now().isoformat(),
            type=step_type,
            content=content,
            tool_name=tool_name,
            tool_input=tool_input,
        ))
        # Also print to console for real-time visibility
        print(f"[Step {step_num}] [{step_type.upper()}] {content[:200]}{'...' if len(content) > 200 else ''}")

    try:
        print("\n" + "=" * 60)
        print(f"[Query] {req.message}")
        print("=" * 60)

        async for msg in query(prompt=req.message, options=agent_options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        reply_chunks.append(block.text)
                        add_step(
                            step_type="text",
                            content=block.text[:500] + ("..." if len(block.text) > 500 else "")
                        )

                    elif isinstance(block, ToolUseBlock):
                        tool_name = block.name
                        tool_input = block.input if hasattr(block, 'input') else {}

                        # Track tools used
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)

                        # Format input for display
                        input_str = json.dumps(tool_input, indent=2) if tool_input else "{}"
                        if len(input_str) > 300:
                            input_str = input_str[:300] + "..."

                        add_step(
                            step_type="tool_use",
                            content=f"Invoking tool: {tool_name}",
                            tool_name=tool_name,
                            tool_input=tool_input if len(json.dumps(tool_input)) < 1000 else {"truncated": True}
                        )

                    elif isinstance(block, ToolResultBlock):
                        result_content = str(block.content) if hasattr(block, 'content') else "Result received"
                        if len(result_content) > 500:
                            result_content = result_content[:500] + "..."

                        add_step(
                            step_type="tool_result",
                            content=result_content
                        )

                    elif isinstance(block, ThinkingBlock):
                        thinking = block.thinking if hasattr(block, 'thinking') else str(block)
                        add_step(
                            step_type="thinking",
                            content=thinking[:500] + ("..." if len(thinking) > 500 else "")
                        )

        print("=" * 60)
        print(f"[Done] Total steps: {step_num}, Tools used: {tools_used}")
        print("=" * 60 + "\n")

    except Exception as e:
        add_step(step_type="error", content=str(e))
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    full_reply = "".join(reply_chunks) if reply_chunks else "No response from agent"

    return VerboseChatResponse(
        reply=full_reply,
        steps=steps,
        total_steps=step_num,
        tools_used=tools_used,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
