# Artifact Library Deploy Skill

This skill automates publishing interactive artifacts to the CSP team's shared Artifact Library.

## What it does

After you build any interactive prototype or demo with Claude, this skill:

1. Asks if you want to publish it to the team library
2. Infers the name, section, description, and tags from conversation context
3. Shows you a confirmation table to review before publishing
4. Pushes the artifact and registers it in artifacts.json
5. Returns a permanent, shareable URL

The homepage at https://ceg-csp.github.io/claude-artifacts/ renders dynamically from artifacts.json. Once registered, your artifact appears automatically in the correct section tab, in search results, and in the library stats.

## Prerequisites (before you start)

You need four things before the setup will work. If you are missing any of these, complete them first.

### A GitHub account

If you do not have one, create a free account at https://github.com/join. Use your ServiceNow email. This takes about 2 minutes.

### Collaborator access to the team repo

Once you have a GitHub account, share your GitHub username with Vinith. He will add you as a collaborator on the ceg-csp/claude-artifacts repo. You will get an email invite — accept it. Without this, you will not be able to publish artifacts.

### Claude Desktop installed

You need the Claude Desktop app (not the browser version). The GitHub integration only works in Claude Desktop because it runs a local server on your machine. Download it from https://claude.ai/download if you do not have it already.

### Node.js installed

The GitHub integration runs through Node.js. If you are not sure whether you have it, open Terminal and type `node --version`. If it shows a version number, you are good. If not, install it from https://nodejs.org (use the LTS version).

## Setup (one-time, ~5 minutes)

Once you have all the prerequisites, follow these steps.

### Step 1: Create a GitHub Personal Access Token

- Go to https://github.com/settings/tokens
- Click "Generate new token (classic)"
- Give it a name like "Claude Desktop"
- Under scopes, check the box next to "repo" (this gives Claude permission to push files)
- Click "Generate token" at the bottom
- Copy the token immediately. You will not be able to see it again.

### Step 2: Configure Claude Desktop

- Open Claude Desktop
- Go to Settings (gear icon at bottom left)
- Click "Developer" in the left sidebar
- Click "Edit Config" under Local MCP Servers
- Paste the following into the config file:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "paste_your_token_here"
      }
    }
  }
}
```

- Replace "paste_your_token_here" with the token you copied in Step 1
- Save the file
- Restart Claude Desktop completely (quit and reopen)

### Step 3: Verify it works

- Open Claude Desktop
- Go to Settings > Developer > Local MCP Servers
- You should see "github" with a green "running" badge
- If it shows "error" or "not running", check that your token is correct and Node.js is installed

### Step 4: Add the Skill (optional but recommended)

If your Claude environment supports custom skills, add the SKILL.md from this folder as a user skill. This tells Claude to automatically offer to publish artifacts when you create them.

If you do not add the skill, the workflow still works. Just tell Claude "publish this to the artifact library at ceg-csp/claude-artifacts" after building any prototype.

## How to use it

1. Build any interactive artifact with Claude the way you normally would
2. When it is ready, say "publish this to the artifact library" (or Claude will ask you if the skill is active)
3. Claude infers the name, section, and description, then shows you a confirmation table
4. Confirm or request changes, and Claude pushes the artifact
5. You get back a permanent URL. Share it with anyone — it works in any browser, no login needed

## Troubleshooting

**GitHub MCP shows "error" or "not running"**
- Make sure Node.js is installed (run `node --version` in Terminal)
- Make sure the token is pasted correctly with no extra spaces
- Restart Claude Desktop after any config change

**Push fails with 404**
- Make sure you have been added as a collaborator on the repo
- Make sure you accepted the invite email from GitHub

**Push fails with 401 or 403**
- Your token may have expired. Generate a new one and update the config.
- Make sure you selected the "repo" scope when creating the token.

## Links

- Artifact Library: https://ceg-csp.github.io/claude-artifacts/
- GitHub Repo: https://github.com/ceg-csp/claude-artifacts
