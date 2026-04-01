---
name: artifact-library-deploy
description: Deploys interactive HTML artifacts to the CSP team's shared artifact library on GitHub Pages. Triggers after any interactive HTML artifact is created. Prompts for artifact name and description, pushes to ceg-csp/claude-artifacts repo, updates the library index page, and returns the permanent shareable URL.
---

# Artifact Library Deploy Skill

This skill automates publishing interactive artifacts to the CSP team's shared library.

## When to Trigger

After ANY interactive HTML artifact is created (prototypes, demos, dashboards, mockups), ask:

> "Would you like to publish this to the team's Artifact Library?"

If yes, proceed with the workflow below.

## Workflow

### Step 1: Collect Info

Ask the user:
1. **Artifact name** — short, descriptive (e.g., "Support Notification Agent", "Prioritization Heat Map")
2. **One-line description** — what does this demo show?
3. **Agent number** (if applicable) — e.g., "Agent 13"
4. **Accent color** (optional) — suggest one based on the content. Format: two hex colors for gradient.

Use the artifact name to generate the folder name. Replace spaces with `%20` in URLs but keep spaces in folder names on GitHub.

### Step 2: Push the Artifact

Push the HTML file to GitHub:

- **Owner:** `ceg-csp` (must be lowercase)
- **Repo:** `claude-artifacts`
- **Branch:** `main`
- **Path:** `[Artifact Name]/index.html`
- **Commit message:** `Update [Artifact Name] - [YYYY-MM-DD]`

If the file already exists (updating), you MUST include the `sha` parameter. Fetch it first:
```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: [Artifact Name]/index.html
```
Then pass the returned `sha` to `github:create_or_update_file`.

### Step 3: Update the Library Index

Fetch the current index.html:
```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: index.html
```

Then update it to add (or update) the artifact card in the "Live Prototypes" grid. Each card follows this template:

```html
<a href="[Folder Name URL-encoded]/" class="artifact-card">
  <div class="card-accent" style="background:linear-gradient(90deg,[color1],[color2]);"></div>
  <div class="card-header">
    <span class="card-agent-badge" style="background:rgba(...);color:[color1];">[Agent Badge]</span>
    <span class="card-status"><span class="dot"></span> Live</span>
  </div>
  <div class="card-title">[Artifact Name]</div>
  <div class="card-desc">[Description]</div>
  <div class="card-outcomes">
    <span class="outcome-tag">[tag1]</span>
    <span class="outcome-tag">[tag2]</span>
  </div>
</a>
```

If the artifact was previously a "Coming Soon" card, replace the placeholder with the live version.

Push the updated index.html with sha.

### Step 4: Confirm to User

Return:
- The permanent live URL: `https://ceg-csp.github.io/claude-artifacts/[Folder Name URL-encoded]/`
- Confirmation that the library index was updated
- The library home URL: `https://ceg-csp.github.io/claude-artifacts/`

## Important Notes

- Owner must always be lowercase `ceg-csp`
- Always fetch sha before updating existing files
- Keep artifact names human-readable (spaces allowed in folder names)
- The library index at root index.html is the team's front door — keep it clean and consistent
- Outcome tags should be 2-4 short phrases describing what the demo shows
- If GitHub MCP is not available (e.g., in claude.ai web), provide terminal commands instead
