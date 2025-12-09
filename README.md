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
```

**What stays inside the container:**
- Skill loading (reading SKILL.md)
- Bash commands
- File read/write operations
- Python script execution
- All filesystem access

**What goes outside:**
- Only the API calls to Claude (model inference)

The container is the isolated Linux environment where all skill execution happens. No Anthropic VM involved in this setup.

## Kubernetes Deployment

Running this image in a Kubernetes pod works for skills. The pod + container together act as your "VM".

**Layers:**
```
Host node → Kubernetes pod → Docker container → Python + Agent SDK + SKILL.md + bash
```

Skills run inside that container filesystem exactly like on your laptop.

### Key pieces for Kubernetes:

**1. Image**
- Build and push your image to your registry
- Use that image in a Deployment spec

**2. Environment variables**
- Set `ANTHROPIC_API_KEY` or gateway variables through a Secret
- Mount them as env vars in the pod

**3. Filesystem for skills**

Option A: Immutable skills baked into image
- Good for quick tests
- Build a new image when you update skills
- No extra volume needed

Option B: Persistent or config driven skills
- Use a PersistentVolumeClaim or ConfigMap to mount skills into `/app/skills` or `/app/.claude/skills`
- Update skills without rebuilding the image

**4. Network**
- Cluster nodes need outbound HTTPS to Anthropic or your internal LLM gateway
- No inbound internet required unless you expose an HTTP API for the agent

**5. Resources**
- Start with: `requests: 1 CPU, 2-4 GB RAM`
- Limits: `2-4 CPU, 8-16 GB RAM`
- Adjust after observing load

**6. Pod lifecycle**
- When the pod starts, Dockerfile CMD runs `python main.py`
- main.py sets cwd to `/app`, wires `setting_sources`, `allowed_tools`, and points skills to `/app/.claude/skills`
- From there the Agent SDK loads SKILL.md and executes tools inside the pod

Deploy this container to Kubernetes as a standard Deployment. The pod becomes your "VM style" runtime. Skills execute inside the pod container on the cluster node.




You end up with two possible deployments:

### Local

You run the Docker container on your laptop.
The Linux image inside the container becomes your small Linux runtime.
Skills run inside that container.

### Cluster

You deploy the same Docker image into a Kubernetes pod.
The pod is your runtime environment.
Skills run inside the pod.

This avoids requesting a dedicated VM from infra.

Only ask for a VM when:

* You want a long-lived host outside Kubernetes.
* You need direct OS control.
* Your platform policy does not allow long-running agent workloads in Kubernetes.
* You plan to add local storage or special networking.

For testing and early dev this container based setup covers everything.
