# CSP Artifact Library

The permanent home for every interactive prototype, demo, and artifact the CSP team builds.

**Live site:** https://ceg-csp.github.io/claude-artifacts/

## What this is

A shared library where interactive artifacts get a permanent, shareable URL. Build something with Claude, publish it here, and the link works forever. Update an artifact later and the same URL shows the latest version. No login required to view.

## How it works

The homepage dynamically renders from `artifacts.json`. Each artifact lives in its own folder as a self-contained `index.html`. A deploy skill automates the full publish workflow from within Claude Desktop.

```
claude-artifacts/
  index.html          <- Homepage (reads from artifacts.json, never needs manual editing)
  artifacts.json      <- Registry of all artifacts (the skill updates this automatically)
  agentic-csm/        <- Agent 13: Support Notification Agent
  csql/               <- CSQL Intelligence Hub
  skill/              <- Deploy automation skill and setup guide
```

## Publishing an artifact

If you have the deploy skill active, Claude will offer to publish after you create any interactive artifact. It infers the name, section, and tags from context, shows you a confirmation table, and pushes everything in two commits.

If you do not have the skill, tell Claude: "Publish this to the artifact library at ceg-csp/claude-artifacts."

The homepage picks up new artifacts automatically. No HTML editing required.

## Getting set up

You need a GitHub account, collaborator access to this repo, Claude Desktop, and Node.js. The full setup guide (about 5 minutes) is here:

**[Setup Guide](https://github.com/ceg-csp/claude-artifacts/blob/main/skill/README.md)**

## Naming convention

All artifact folders use lowercase with hyphens. Examples: `agentic-csm/`, `csql/`, `account-360/`. No spaces, no uppercase. The skill enforces this automatically.

## Homepage features

- Tab-based navigation across 5 sections (Product Management, Analytics, GTM Tooling, Program Management, Misc)
- Cmd+K spotlight search across all artifacts
- Dark/light mode toggle (saved to browser)
- Grid/list view toggle
- Contributors tab (live from GitHub API)
- Activity feed (live commit history)
- Mobile responsive

## Links

- **Live site:** https://ceg-csp.github.io/claude-artifacts/
- **Setup guide:** https://github.com/ceg-csp/claude-artifacts/blob/main/skill/README.md
- **Deploy skill:** https://github.com/ceg-csp/claude-artifacts/blob/main/skill/SKILL.md
