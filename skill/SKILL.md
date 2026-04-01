---
name: artifact-library-deploy
description: Deploys interactive HTML artifacts to the CSP team's shared artifact library on GitHub Pages. Triggers after any interactive HTML artifact is created. Prompts for artifact name, description, and section. Pushes artifact, updates the library homepage (card + search index + tab count), and returns the permanent shareable URL.
---

# Artifact Library Deploy Skill

This skill automates publishing interactive artifacts to the CSP team's shared library and ensures every artifact is automatically visible on the homepage.

## When to Trigger

After ANY interactive HTML artifact is created (prototypes, demos, dashboards, mockups), ask:

> "Would you like to publish this to the team's Artifact Library?"

If yes, proceed with the workflow below.

## Workflow

### Step 1: Collect Info

Ask the user for all of the following in one go:

1. **Artifact name** — short, descriptive (e.g., "Support Notification Agent", "Account 360 Dashboard")
2. **One-line description** — what does this demo show? Keep under 120 characters.
3. **Section** — which tab should this appear under? Options:
   - Product Management (panel id: p0)
   - Analytics (panel id: p1)
   - GTM Tooling (panel id: p2)
   - Program Management (panel id: p3)
   - Misc (panel id: p4)
4. **Agent number** (if applicable) — e.g., "Agent 13". Use "Tool" or "Demo" if not agent-related.
5. **Tags** — 2-4 short keywords that describe capabilities (e.g., "Real-time alerts", "Portfolio scoring")
6. **Accent color** — suggest one based on the content. Pick from the existing palette:
   - Rose: `var(--rose)` / `var(--orange)` — for support, alerts, risk
   - Accent/Purple: `var(--accent)` / `var(--purple)` — for analytics, scoring
   - Amber/Orange: `var(--amber)` / `var(--orange)` — for meetings, collaboration
   - Green: `var(--green)` / `var(--accent)` — for health, adoption, positive signals

### Step 2: Push the Artifact HTML

Push the HTML file to GitHub:

- **Owner:** `ceg-csp` (MUST be lowercase)
- **Repo:** `claude-artifacts`
- **Branch:** `main`
- **Path:** `[Artifact Name]/index.html`
- **Commit message:** `Add [Artifact Name] - [YYYY-MM-DD]`

If updating an existing artifact, fetch the sha first:
```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: [Artifact Name]/index.html
```
Then pass the returned `sha` to `github:create_or_update_file`. Use commit message `Update [Artifact Name] - [YYYY-MM-DD]`.

### Step 3: Update the Library Homepage (CRITICAL)

This step ensures the artifact appears on the homepage. It requires TWO updates to the index.html file: adding an HTML card AND registering in the search index.

#### 3a: Fetch the current index.html

```
github:get_file_contents -> owner: ceg-csp, repo: claude-artifacts, path: index.html
```

Save the returned `sha` — you will need it to push the update.

#### 3b: Add the artifact card to the correct section panel

Find the panel div for the target section. The panel IDs are:
- Product Management: `id="p0"`
- Analytics: `id="p1"`
- GTM Tooling: `id="p2"`
- Program Management: `id="p3"`
- Misc: `id="p4"`

**If the panel currently has an empty state** (contains `<div class="empty">`), replace the entire empty div with a grid containing the new card:

```html
<div class="grid" id="grid-p[N]">
  [NEW CARD HTML]
</div>
```

**If the panel already has a grid**, add the new card inside the existing grid.

**Card HTML template:**

```html
<a href="[Folder Name URL-encoded]/" class="card">
  <div class="bar" style="background:linear-gradient(90deg,[color1],[color2]);"></div>
  <div class="card-top">
    <span class="badge" style="background:[color1-bg];color:[color1];">[Agent Badge]</span>
    <span class="st live"><span class="d"></span> Live</span>
  </div>
  <h3>[Artifact Name]</h3>
  <div class="desc">[Description]</div>
  <div class="tags">
    <span class="tag" style="background:[color1-bg];color:[color1];">[Tag 1]</span>
    <span class="tag" style="background:[color1-bg];color:[color1];">[Tag 2]</span>
  </div>
</a>
```

**If the artifact replaces a "Coming Soon" placeholder**, find the placeholder card (has class `ph`) with the matching name and replace it entirely with the live card above.

#### 3c: Add the artifact to the JavaScript search registry

Find the `const artifacts=[` array in the script tag. Add a new entry:

```javascript
{name:'[Artifact Name]',section:'[Section Name]',desc:'[Description]',tags:['tag1','tag2','tag3'],url:'[Folder Name URL-encoded]/',live:true,agent:'[Agent Badge]',color:'[color1 CSS var]'}
```

If the artifact was previously listed as `live:false`, update it to `live:true` and add the `url`.

#### 3d: Update the tab count badge

Find the tab for the target section and update the count span:
- Change the count number (e.g., `0` to `1`, `1` to `2`)
- If the count was `0`, change `class="ct zero"` to `class="ct has"`

#### 3e: Update hero stats

Find the hero stat that shows live artifact count and increment it.

#### 3f: Push the updated index.html

```
github:create_or_update_file -> owner: ceg-csp, repo: claude-artifacts, path: index.html, sha: [sha from step 3a]
```

Commit message: `Add [Artifact Name] to library index - [YYYY-MM-DD]`

### Step 4: Confirm to User

Return all three pieces of information:

1. **Artifact URL:** `https://ceg-csp.github.io/claude-artifacts/[Folder Name URL-encoded]/`
2. **Library URL:** `https://ceg-csp.github.io/claude-artifacts/`
3. **Confirmation:** "Published to [Section Name]. The artifact card, search index, and tab counts have been updated on the homepage."

Remind the user it may take 1-2 minutes for GitHub Pages to rebuild, and to hard refresh (Cmd+Shift+R) if they see the old version.

## Important Notes

- Owner must ALWAYS be lowercase `ceg-csp`
- Always fetch sha before updating any existing file
- Keep artifact names human-readable (spaces allowed in folder names)
- URL-encode spaces as `%20` in href attributes
- The index.html is the team's front door — both the visible cards AND the JS search registry must be updated
- If you only update the card but not the search registry, AI search will not find the artifact
- If you only update the registry but not the card, the artifact will not be visible in the tab
- Both must always be updated together in a single push
- Outcome tags should be 2-4 short keyword phrases
- If GitHub MCP is not available (e.g., in claude.ai web), provide terminal commands instead
- After updating, always verify by fetching the file again to confirm the changes landed
