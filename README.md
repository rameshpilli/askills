# Claude Agent SDK Docker Environment

A Docker-based environment for running the Claude Agent SDK with skills.

## Project Structure

```
AgentSkills/
├── Dockerfile
├── pyproject.toml
├── app/
│   └── main.py
└── skills/
    ├── pdf/
    ├── xlsx/
    ├── pptx/
    ├── docx/
    └── ... (17 skills total)
```

## Quick Start

### 1. Build the Image

```bash
docker build -t claude-agent-dev .
```

### 2. Run the Container

```bash
docker run -it --rm \
  -e ANTHROPIC_API_KEY=your_api_key_here \
  claude-agent-dev
```

### 3. Use It

Type prompts and press Enter. Type `exit` to stop.

## Included Skills

From [anthropics/skills](https://github.com/anthropics/skills):

| Skill | Description |
|-------|-------------|
| `pdf` | PDF manipulation and form filling |
| `xlsx` | Excel spreadsheet handling |
| `pptx` | PowerPoint presentations |
| `docx` | Word documents |
| `frontend-design` | Frontend UI/UX design |
| `canvas-design` | Canvas-based design |
| `algorithmic-art` | Generative art |
| `mcp-builder` | MCP server builder |
| `skill-creator` | Create new skills |
| `webapp-testing` | Web app testing |
| `web-artifacts-builder` | Web artifacts |
| `brand-guidelines` | Brand identity |
| `internal-comms` | Internal communications |
| `slack-gif-creator` | Slack GIFs |
| `theme-factory` | Theme generation |
| `doc-coauthoring` | Document collaboration |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | API key for Anthropic |
| `LLM_GATEWAY_URL` | No | Custom gateway URL |

## Adding Custom Skills

1. Create a folder in `skills/` with a `SKILL.md` file
2. Rebuild: `docker build -t claude-agent-dev .`

## How It Works

```
┌─────────────────────────────────────────────┐
│  Docker Container                           │
│  ┌───────────────────────────────────────┐  │
│  │  Python 3.11 + Claude Agent SDK       │  │
│  │  main.py → loads skills from          │  │
│  │            /app/.claude/skills/       │  │
│  │                                       │  │
│  │  Skills execute HERE (Bash, Python)   │  │
│  └───────────────────┬───────────────────┘  │
└──────────────────────┼──────────────────────┘
                       │ HTTPS only
                       ▼
              Claude API / Gateway
```

All skill execution happens inside the container. Only API calls go out.


┌─────────────────────────────────────────────────────────────┐
│  Your MacBook (Host)                                        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Docker Desktop                                       │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Container (python:3.11-slim)                   │  │  │
│  │  │                                                 │  │  │
│  │  │  • Python 3.11                                  │  │  │
│  │  │  • Claude Agent SDK                             │  │  │
│  │  │  • main.py (your entrypoint)                    │  │  │
│  │  │  • /app/.claude/skills/* (skill definitions)    │  │  │
│  │  │  • /bin/bash (for Bash tool)                    │  │  │
│  │  │                                                 │  │  │
│  │  │  Skills execute HERE                            │  │  │
│  │  └──────────────────┬──────────────────────────────┘  │  │
│  └─────────────────────┼─────────────────────────────────┘  │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ HTTPS (API calls only)
                         ▼
              ┌─────────────────────┐
              │  Claude API         │
              │  (or your gateway)  │
              └─────────────────────┘

What stays inside the container:
- Skill loading (reading SKILL.md)
- Bash commands
- File read/write operations
- Python script execution
- All filesystem access

What goes outside:
- Only the API calls to Claude (model inference)

- The container is our isolated Linux environment where all skill execution happens. No Anthropic VM involved in this setup.


- Running this image in a Kubernetes pod works for skills. The pod + container together act as your “VM”.

Think of the layers:

Host node
→ Kubernetes pod
→ Your Docker container
→ Python + Agent SDK + SKILL.md + bash

Skills run inside that container filesystem exactly like on your laptop.