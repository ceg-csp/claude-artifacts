---
name: artifact-library-deploy
description: Deploys interactive HTML artifacts to the CSP team's shared artifact library on GitHub Pages. Triggers after any interactive HTML artifact is created. Pushes artifact HTML and updates artifacts.json registry. The homepage dynamically renders everything from the JSON.
---

# Artifact Library Deploy Skill

This skill automates publishing interactive artifacts to the CSP team's shared library.

## When to Trigger

After ANY interactive HTML artifact is created (prototypes, demos, dashboards, mockups), ask:

> "Would you like to publish this to the team's Artifact Library?"

If yes, proceed with the workflow below.

## Workflow

### Step 1: Collect Info

Ask the user for all of the following:

1. **Artifact name** — short, descriptive (e.g., "Support Notification Agent")
2. **One-line description** — under 120 characters
3. **Section** — which tab:
   - Product Management
   - Analytics
   - GTM Tooling
   - Program Management
   - Misc
4. **Agent number** (if applicable) — e.g., "Agent 13". Use "Tool" or "Demo" if not agent-related.
5. **Tags** — 2-4 short keywords (e.g., "Real-time alerts", "Portfolio scoring")
6. **Accent colors** — pick from palette:
   - Rose/Orange: `var(--rose)` / `var(--orange)` + `var(--rose-bg)`
   - Accent/Purple: `var(--accent)` / `var(--purple)` + `var(--accent-bg)`
   - Amber/Orange: `var(--amber)` / `var(--orange)` + `var(--amber-bg)`
   - Green/Teal: `var(--green)` / `var(--teal)` + `var(--green-bg)`
   - Purple: `var(--purple)` / `var(--accent)` + `var(--purple-bg)`

### Step 2: Push the Artifact HTML

- **Owner:** `ceg-csp` (MUST be lowercase)
- **Repo:** `claude-artifacts`
- **Branch:** `main`
- **Path:** `[Artifact Name]/index.html`
- **Commit message:** `Add [Artifact Name] - [YYYY-MM-DD]`

If updating an existing artifact, fetch sha first:
```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: [Artifact Name]/index.html
```
Then include `sha` in the update call.

### Step 3: Update artifacts.json (CRITICAL)

This is the ONLY file that needs updating for the homepage. No HTML editing required.

#### 3a: Fetch current artifacts.json
```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: artifacts.json
```
Save the returned `sha`.

#### 3b: Parse the JSON and add the new artifact

Add a new entry to the array:
```json
{
  "name": "[Artifact Name]",
  "section": "[Section Name]",
  "desc": "[Description]",
  "tags": ["Tag 1", "Tag 2", "Tag 3"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "url": "[Folder Name URL-encoded]/",
  "live": true,
  "agent": "[Agent Badge]",
  "color1": "var(--rose)",
  "color2": "var(--orange)",
  "colorBg": "var(--rose-bg)",
  "added": "[YYYY-MM-DD]"
}
```

- `keywords` should include 8-12 search terms that someone might use to find this artifact (broader than tags)
- `url` must be URL-encoded (spaces become %20)
- If updating an existing artifact, find the entry by name and update its fields

#### 3c: Push updated artifacts.json
```
github:create_or_update_file -> owner: ceg-csp, repo: claude-artifacts, path: artifacts.json, sha: [sha from 3a]
```
Commit message: `Register [Artifact Name] in library - [YYYY-MM-DD]`

That is it. The homepage reads artifacts.json on load and dynamically renders all cards, tab counts, stats, and search index. No HTML editing needed.

### Step 4: Confirm to User

Return:
1. **Artifact URL:** `https://ceg-csp.github.io/claude-artifacts/[Folder Name URL-encoded]/`
2. **Library URL:** `https://ceg-csp.github.io/claude-artifacts/`
3. **Confirmation:** "Published to [Section Name]. The artifact will appear on the homepage automatically."

Remind user to hard refresh (Cmd+Shift+R) if they see the old version.

## Important Notes

- Owner must ALWAYS be lowercase `ceg-csp`
- Always fetch sha before updating any existing file
- The homepage dynamically reads artifacts.json — you NEVER need to edit index.html
- Keep keywords broad — include terms users might naturally search for
- URL-encode spaces as %20 in the url field
- If GitHub MCP is not available (e.g., in claude.ai web), provide terminal commands instead
