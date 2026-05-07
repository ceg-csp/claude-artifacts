# Deploy to GitHub Pages Skill

## Trigger

Activate when the user says any of:
- "deploy to GitHub Pages"
- "deploy this artifact"
- "push to GitHub Pages"
- "publish this to the library"
- "deploy to GitHub"

Also activate when, after completing an HTML artifact, the user confirms deployment.

## Context

- Repo: `ceg-csp/claude-artifacts` on GitHub Pages
- Local clone: `~/repos/claude-artifacts`
- Homepage: `https://ceg-csp.github.io/claude-artifacts/`
- Registry: `artifacts.json` at repo root (drives the homepage dynamically)
- Each artifact lives at `<name>/index.html` where `<name>` is kebab-case
- URLs are permanent — updates overwrite index.html, link never changes

## Workflow

### Step 1: Identify the artifact

Determine what is being deployed:
- If an HTML artifact was just created in this conversation, use that
- If the user references a file path, use that
- If ambiguous, ask: "Which artifact are you deploying?"

Determine the folder name (kebab-case, e.g. `product-adoption-dashboard`).
- For new artifacts: infer from the artifact name or ask
- For updates: match to an existing folder in the repo

### Step 2: Pull latest

```bash
cd ~/repos/claude-artifacts && git pull origin main
```

If there are merge conflicts, stop and tell the user.

### Step 3: Check if new or update

```bash
ls ~/repos/claude-artifacts/<name>/index.html 2>/dev/null && echo "EXISTS" || echo "NEW"
```

- **EXISTS** → This is an update. Skip to Step 5.
- **NEW** → This is a new artifact. Continue to Step 4.

### Step 4: Registry entry (new artifacts only)

Read the current registry:

```bash
cat ~/repos/claude-artifacts/artifacts.json
```

Infer the best section from existing entries (e.g. "Product Management", "Learning & Enablement").

Show the user a confirmation table:

| Field | Value |
|-------|-------|
| Name | Human-readable name |
| Section | Inferred section |
| Description | One-line description |
| Tags | 2-4 tags |
| Agent | Agent name |

Wait for the user to confirm or edit before proceeding.

On confirm, update artifacts.json locally — append the new entry with this structure:

```json
{
  "name": "Display Name",
  "section": "Section Name",
  "desc": "One-line description.",
  "tags": ["Tag1", "Tag2"],
  "keywords": ["search", "terms", "for", "homepage", "cmd-k"],
  "url": "<name>/",
  "live": true,
  "agent": "Agent Name",
  "color1": "var(--accent)",
  "color2": "var(--green)",
  "colorBg": "var(--accent-bg)",
  "added": "YYYY-MM-DD"
}
```

Write the updated JSON back to `~/repos/claude-artifacts/artifacts.json`.

NEVER skip this step for new artifacts.

### Step 5: Write the HTML

```bash
mkdir -p ~/repos/claude-artifacts/<name>
```

Write the full HTML content to `~/repos/claude-artifacts/<name>/index.html`.

If the HTML was produced in this conversation, write it directly from context.
If the user provides a file path, copy it:

```bash
cp <source-path> ~/repos/claude-artifacts/<name>/index.html
```

### Step 6: Commit and push

```bash
cd ~/repos/claude-artifacts
git add -A
git commit -m "deploy: <name>"
git push origin main
```

If push fails due to auth, tell the user to run `git push origin main` manually from their terminal.

### Step 7: Return confirmation

Always return this table after a successful deploy:

| Field | Value |
|-------|-------|
| **Artifact** | Display Name |
| **Repo Path** | `<name>/index.html` |
| **Shareable Link** | `https://ceg-csp.github.io/claude-artifacts/<name>/` |
| **Library URL** | `https://ceg-csp.github.io/claude-artifacts/` |
| **Status** | Live (or Updated) |

Note: GitHub Pages may take 1-2 minutes to reflect changes after push.

## Rules

1. ALWAYS `git pull` before writing anything
2. NEVER skip artifacts.json update for new artifacts
3. NEVER modify artifacts.json for updates unless the user explicitly asks
4. URL is permanent — updates overwrite index.html at the same path
5. Show registry table and wait for confirmation before writing new entries
6. If the HTML file is provided as a path, copy it; if it was built in conversation, write it directly
7. All folder names must be kebab-case
8. Always include keywords in artifacts.json — these power the Cmd+K search on the homepage
