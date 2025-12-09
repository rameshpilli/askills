---
name: hello-world
description: A simple example skill that demonstrates the skills system
---

# Hello World Skill

This is an example skill to verify that skills loading is working correctly.

## When to use this skill

Use this skill when:
- The user asks to test skills
- The user says "hello" or wants a greeting
- You need to verify the skills system is working

## How it works

When invoked, respond with a friendly greeting that confirms:
1. The skill was loaded successfully
2. The Claude Agent SDK is running in Docker
3. Skills from the `.claude/skills` directory are accessible

## Example response

```
Hello from the Hello World skill!

✓ Skills loading is working correctly
✓ Running in Docker container
✓ Ready to process your requests

How can I help you today?
```
