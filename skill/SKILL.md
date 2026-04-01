---
name: artifact-library-deploy
description: Deploys interactive HTML artifacts to the CSP team's shared artifact library on GitHub Pages. Triggers after any interactive HTML artifact is created. Pushes artifact HTML and updates artifacts.json registry. The homepage dynamically renders everything from the JSON.
---

# Artifact Library Deploy Skill

This skill automates publishing interactive artifacts to the CSP team's shared library.

## When to Trigger

After ANY interactive HTML artifact is created (prototypes, demos, dashboards, mockups), ask:

> "Would you like me to deploy this to GitHub Pages?"

If yes, proceed with the workflow below. Execute ALL steps — never stop after pushing the HTML.

## Workflow

### Step 1: Infer Registry Entry (DO NOT ask 6 separate questions)

Read the current `artifacts.json` to understand existing sections and naming patterns:

```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: artifacts.json
```

Save the returned `sha` for later.

Using conversation context, infer ALL fields and present a single confirmation table:

> **Deploying to Artifact Library**
>
> | Field | Value |
> |---|---|
> | **Name** | [inferred from artifact title] |
> | **Section** | [best match from existing sections, or suggest new] |
> | **Description** | [one-line, under 120 chars] |
> | **Tags** | [2-4 short keywords] |
> | **Agent** | [agent name if applicable, otherwise "Tool" or "Demo"] |
>
> Confirm to deploy, or tell me what to change.

**Section inference rules:**
- CSP prototypes, product features, demos, PRDs → Product Management
- Data dashboards, Snowflake queries, analytics tools → Analytics
- Sales tooling, AE/CSM enablement, account briefs → GTM Tooling
- Ops workflows, process tools, governance → Program Management
- Anything else → Misc

**Color auto-assignment by section (must use actual CSS variable names from index.html):**
- Product Management: `var(--accent)` / `var(--green)` / `var(--accent-bg)`
- Analytics: `var(--purple)` / `var(--accent)` / `var(--purple-bg)`
- GTM Tooling: `var(--amber)` / `var(--orange)` / `var(--amber-bg)`
- Program Management: `var(--green)` / `var(--teal)` / `var(--green-bg)`
- Misc: `var(--rose)` / `var(--orange)` / `var(--rose-bg)`

**Valid CSS color variables:** `--accent`, `--green`, `--purple`, `--amber`, `--rose`, `--orange`, `--teal` and their `-bg` variants. Do NOT use `--blue` — it does not exist in the stylesheet. Use `--accent` for blue.

Wait for user confirmation before proceeding. If user requests changes, update and re-confirm.

### Step 2: Push the Artifact HTML

- **Owner:** `ceg-csp` (MUST be lowercase)
- **Repo:** `claude-artifacts`
- **Branch:** `main`
- **Path:** `[artifact-name]/index.html` (lowercase, hyphens for spaces)
- **Commit message:** `Update [artifact-name] - [YYYY-MM-DD]`

If updating an existing artifact, fetch sha first:
```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: [artifact-name]/index.html
```
Then include `sha` in the update call.

### Step 3: Update artifacts.json (CRITICAL — NEVER SKIP)

This step is MANDATORY. The homepage reads artifacts.json on load. If you skip this, the artifact exists but is invisible in the library.

Parse the JSON array from Step 1 and append the new entry:

```json
{
  "name": "[Artifact Name]",
  "section": "[Section Name]",
  "desc": "[Description under 120 chars]",
  "tags": ["Tag 1", "Tag 2", "Tag 3"],
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "url": "[folder-name]/",
  "live": true,
  "agent": "[Agent Badge]",
  "color1": "[from section color map]",
  "color2": "[from section color map]",
  "colorBg": "[from section color map]",
  "added": "[YYYY-MM-DD]"
}
```

**Field notes:**
- `keywords`: 8-12 search terms broader than tags — think about what someone would type to find this
- `url`: folder name, URL-encoded if spaces (prefer lowercase hyphens to avoid encoding)
- `color1`, `color2`, `colorBg`: MUST use valid CSS variables from the color map above. Never use `var(--blue)`.
- If updating an existing artifact, find the entry by name and update its fields

Push updated artifacts.json using the sha saved from Step 1:
```
github:create_or_update_file -> owner: ceg-csp, repo: claude-artifacts, path: artifacts.json, sha: [saved sha]
```
Commit message: `Update artifacts.json - add [Artifact Name]`

### Step 4: Return Structured Confirmation

Always return this exact format after successful deployment:

> **Deployment Complete**
>
> | | |
> |---|---|
> | **Artifact** | [Name] |
> | **Repo Path** | `ceg-csp/claude-artifacts/[folder]/index.html` |
> | **Shareable Link** | https://ceg-csp.github.io/claude-artifacts/[folder]/ |
> | **Artifact Library** | https://ceg-csp.github.io/claude-artifacts/ |
> | **Commit 1** | `[sha]` — [artifact commit message] |
> | **Commit 2** | `[sha]` — [registry commit message] |
> | **Status** | Live |

## Important Notes

- Owner must ALWAYS be lowercase `ceg-csp`
- Always fetch sha before updating any existing file
- The homepage dynamically reads artifacts.json — you NEVER need to edit index.html
- Keep keywords broad — include terms users might naturally search for
- Prefer lowercase-hyphen folder names (e.g., `csql/` not `CSQL Intelligence Hub/`)
- NEVER use `var(--blue)` or `var(--blue-bg)` — these do not exist. Use `var(--accent)` / `var(--accent-bg)` for blue.
- If GitHub MCP is not available (e.g., in claude.ai web), provide terminal commands instead
- Hard refresh (Cmd+Shift+R) may be needed if user sees cached version
