# Artifact Library Deploy Skill

This skill automates publishing interactive artifacts to the CSP team's shared Artifact Library.

## What it does

After you build any interactive prototype or demo with Claude, this skill:

1. Asks if you want to publish it to the team library
2. Collects the artifact name and description
3. Pushes it to our shared GitHub repo
4. Updates the library index page with a new card
5. Returns a permanent, shareable URL

## Setup (one-time, ~5 minutes)

### 1. Get a GitHub Personal Access Token

- Go to https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Give it a name like "Claude Desktop"
- Select the `repo` scope
- Copy the token

### 2. Configure Claude Desktop

- Open Claude Desktop
- Go to Settings (gear icon) > Developer > Local MCP Servers
- Click "Edit Config"
- Add or update the github server:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

- Save and restart Claude Desktop
- You should see "github" with a green "running" badge in MCP servers

### 3. Add the Skill (optional)

If your Claude environment supports custom skills, add the SKILL.md from this folder. Otherwise the workflow works manually — just tell Claude to push your artifact to `ceg-csp/claude-artifacts`.

## Usage

Just build any interactive artifact with Claude and say "publish this to the artifact library" or wait for Claude to ask you.

## Links

- Artifact Library: https://ceg-csp.github.io/claude-artifacts/
- GitHub Repo: https://github.com/ceg-csp/claude-artifacts
