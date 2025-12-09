#!/usr/bin/env python3
"""
Claude Agent SDK Entrypoint with Skills Support

This script:
1. Sets up the skills directory structure expected by the Claude Agent SDK
2. Configures the agent with filesystem-based skills loading
3. Runs a simple CLI loop for interactive prompts

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
import os
import sys
from pathlib import Path


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


async def run_agent_loop():
    """
    Run the main agent interaction loop.

    This loop:
    1. Reads prompts from stdin
    2. Sends them to the Claude Agent SDK
    3. Prints responses to stdout

    The agent is configured to:
    - Load skills from .claude/skills via setting_sources=["project"]
    - Allow Skill, Read, Write, and Bash tools
    - Use the working directory from CLAUDE_AGENT_CWD
    """
    # Import Claude Agent SDK
    try:
        from claude_agent_sdk import (
            ClaudeSDKClient,
            ClaudeAgentOptions,
            AssistantMessage,
            TextBlock,
            ToolUseBlock,
            ResultMessage,
        )
    except ImportError:
        print("Error: claude-agent-sdk is not installed.")
        print("Install it with: pip install claude-agent-sdk")
        sys.exit(1)

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    gateway_url = os.environ.get("LLM_GATEWAY_URL")

    if not api_key and not gateway_url:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Run the container with: docker run -e ANTHROPIC_API_KEY=your_key ...")
        sys.exit(1)

    # Get working directory
    cwd = os.environ.get("CLAUDE_AGENT_CWD", "/app")

    # Configure the agent
    # setting_sources=["project"] enables loading skills from .claude/skills/
    # allowed_tools includes Skill for invoking skills, plus Read/Write/Bash
    # for skills that need filesystem or shell access
    options = ClaudeAgentOptions(
        cwd=cwd,
        # Load settings and skills from project directory
        # "project" looks for .claude/settings.json and .claude/skills/
        setting_sources=["project"],
        # Tools available to the agent
        # - Skill: invoke custom skills from .claude/skills/
        # - Read: read files (required by many skills)
        # - Write: write files (required by many skills)
        # - Bash: execute shell commands (required by some skills)
        # - Edit: edit files with string replacement
        # - Glob: find files by pattern
        # - Grep: search file contents
        allowed_tools=["Skill", "Read", "Write", "Bash", "Edit", "Glob", "Grep"],
        # Accept file edits automatically for smoother operation
        # Change to "plan" if you want approval prompts
        permission_mode="acceptEdits",
    )

    print("\n" + "=" * 60)
    print("Claude Agent SDK - Interactive Mode")
    print("=" * 60)
    print(f"Working directory: {cwd}")
    print("Type your prompts and press Enter. Type 'exit' or 'quit' to stop.")
    print("=" * 60 + "\n")

    # Use ClaudeSDKClient for multi-turn conversation support
    async with ClaudeSDKClient(options=options) as client:
        while True:
            try:
                # Read prompt from stdin
                print("You: ", end="", flush=True)
                prompt = input().strip()

                # Check for exit commands
                if prompt.lower() in ("exit", "quit", "q"):
                    print("Goodbye!")
                    break

                # Skip empty prompts
                if not prompt:
                    continue

                # Send prompt to agent
                await client.query(prompt)

                # Process and print response
                print("\nClaude: ", end="", flush=True)
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                print(block.text, end="", flush=True)
                            elif isinstance(block, ToolUseBlock):
                                # Show tool usage for transparency
                                print(f"\n[Using tool: {block.name}]", flush=True)
                    elif isinstance(message, ResultMessage):
                        # Show completion stats
                        if message.total_cost_usd:
                            print(f"\n[Cost: ${message.total_cost_usd:.4f}]", end="")

                print("\n")  # Newline after response

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except EOFError:
                print("\n\nEnd of input. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Try again or type 'exit' to quit.\n")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Claude Agent SDK Container Starting...")
    print("=" * 60)

    # Step 1: Set up skills directory structure
    print("\n[Step 1] Setting up skills directory...")
    setup_skills_directory()

    # Step 2: Run the agent loop
    print("\n[Step 2] Starting agent...")
    asyncio.run(run_agent_loop())


if __name__ == "__main__":
    main()
