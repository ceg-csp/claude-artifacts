---
name: cip-generator
description: Generate a Customer Impact Plan CIP deck automatically for any ServiceNow Impact customer. Triggers on any message containing Customer Impact Plan, CIP deck, generate CIP, or Impact Plan for an account. Fetches all data from Snowflake and ValueMelody, fills the master PPTX template with surgical XML edits, and returns a download-ready deck. Use this skill whenever a CSM asks to generate, create, or build a CIP for any account.
version: 1.2.0
last_updated: 2026-04-06
changelog:
  1.2.0: Six reliability improvements — dynamic SCRIPTS path, input validation gate,
         label-anchored 25% field replacement, sample_data.json reference file,
         slide5 empty cell fallback for col3, version header added to SKILL.md
  1.1.0: Hardened pipeline — cip_runner.py replaces inline slide editing, patched
         pack.py with OPC rels path normalization, clean.py removed from workflow,
         3-call Snowflake data fetch pattern, data normalization dict
  1.0.0: Initial skill — inline XML editing, single Snowflake call, basic pack/validate
---

# CIP Generator Skill

## Purpose
Generate a fully populated Customer Impact Plan PPTX deck for a given account by fetching live data from Snowflake and ValueMelody and performing surgical XML edits on the master template. No manual data entry required.

## Template Location
The master template lives at:
/mnt/skills/user/cip-generator/assets/CIP_MASTER_TEMPLATE.pptx

Always use this file as the base. Never use a user-uploaded file unless explicitly instructed.

## Trigger
Any message containing: Customer Impact Plan, CIP deck, generate CIP, create CIP, build CIP, Impact Plan for account.

---

## Workflow

### Step 1: Extract Account Details from Prompt
Parse the incoming message for:
- Account Name
- Account Number

If either is missing, ask once:
"Please provide both the Account Name and Account Number to generate the CIP."

Do not proceed without both values.

---

### Step 2: Validate Account via Account Lookup
Read and follow: /mnt/skills/organization/account-lookup/SKILL.md

Use both Account Name and Account Number to confirm the account exists and resolve any disambiguation. Store confirmed ACCOUNT_NUMBER for all subsequent queries.

---

### Step 3: Snowflake Data Fetch

IMPORTANT: Make 3 separate targeted calls — not one broad call. Broad calls overflow the
context window and require fragile bash file parsing. Targeted calls stay in context and
return cleanly structured data.

#### Call 3A — Account basics and Impact metrics
Question to send:
"For account [ACCOUNT_NUMBER]: account full name, customer since date, CSM name,
instance name(s), current release version, overall health score (HealthScan),
Impact program type, accelerators raised count, on-demand training completed count,
instance observer seats used and total, impact app usage percentage, critical apps
undeployed percentage, past completed accelerator names (max 6), and deliverables
status for: Objectives and Outcomes, Customer Impact Plan, Capability Map, Product
Adoption Roadmap, Value Insights."

Extract and store as structured fields:
- account_name (full, for slide 1)
- account_short (first word or acronym, for slide 4 title)
- csm_name
- customer_since (format: DD MMM YYYY)
- time_with_impact (compute: years since customer_since, format as X+ years)
- instance (instance name)
- release (current release name e.g. Yokohama)
- health_score (display N/A if unavailable)
- accelerators_raised (count)
- on_demand_training (count, display 0 if none)
- observer_seats (format X/5, display N/A if unavailable)
- impact_app_usage (display as X%)
- critical_apps_undeployed (display as X%)
- past_accelerators (list of names, max 6)

#### Call 3B — Licensing table
Question to send:
"For account [ACCOUNT_NUMBER]: full active product licensing table with product code,
product full name, product unit/type, and quantity for all active products."

Extract and store as:
- licensing_rows: list of {code, name, type, units} objects, up to 10 rows for the
  template (use the highest-value products if more than 10 exist)

#### Call 3C — Accelerators and initiatives
Question to send:
"For account [ACCOUNT_NUMBER]: list all completed Impact accelerators by name, all
recommended Impact accelerators by name, active key initiatives (max 3), planned
technical accelerators for the Gantt (max 4), training credits count and earliest
expiry date."

Extract and store as:
- completed_accelerators (list of names)
- recommended_accelerators (list of names)
- initiative_1, initiative_2, initiative_3 (Gantt initiative names)
- training_credits (count or N/A)
- training_expiry (date string or N/A)

DATA FALLBACK RULE: For any field where data is unavailable, store the string "N/A".
Never leave a field blank. Never hallucinate values.

---

### Step 4: ValueMelody Data Fetch
Call ValueMelody:VE_Pipeline for the confirmed account.

Extract specifically:
- adoption_gaps: products in LicensedAndNotUsedCapabilities or LicensedAndUnderutilizedCapabilities
  across all outcomes — use the top 4 unique product areas as the adoption gap bullets
- If ValueMelody returns richer adoption gap data than Snowflake, use ValueMelody's version

Store as:
- adoption_gaps (list of 4 product area strings for slide 4 bullets)

If ValueMelody is unavailable or returns an error, continue with Snowflake data only
and set adoption_gaps to ["N/A", "", "", ""].

---

### Step 5: Build Data Dict and Run CIP Runner

After all data is collected, assemble a single Python dict (or JSON) with ALL fields
before touching any XML. This is the normalization contract — every slide edit reads
from this dict, nothing is hardcoded inline.

```python
data = {
    "account_name":             "[from Call 3A]",
    "account_short":            "[first word or acronym]",
    "csm_name":                 "[from Call 3A]",
    "customer_since":           "[from Call 3A, format: DD MMM YYYY]",
    "time_with_impact":         "[computed, format: X+ years]",
    "instance":                 "[from Call 3A]",
    "release":                  "[from Call 3A]",
    "health_score":             "[from Call 3A, or N/A]",
    "accelerators_raised":      "[from Call 3A]",
    "on_demand_training":       "[from Call 3A, or 0]",
    "observer_seats":           "[from Call 3A, or N/A]",
    "impact_app_usage":         "[from Call 3A, as X%]",
    "critical_apps_undeployed": "[from Call 3A, or N/A]",
    "initiative_1":             "[from Call 3C, or empty string]",
    "initiative_2":             "[from Call 3C, or empty string]",
    "initiative_3":             "[from Call 3C, or empty string]",
    "training_credits":         "[from Call 3C, or N/A]",
    "training_expiry":          "[from Call 3C, or N/A]",
    "past_accelerators":        ["[name1]", "[name2]", ...],  # max 6
    "adoption_gaps":            ["[gap1]", "[gap2]", "[gap3]", "[gap4]"],
    "licensing_rows": [
        {"code": "[PRODXXXXX]", "name": "[full name]", "type": "[unit type]", "units": "[qty]"},
        ...  # up to 10 rows
    ],
    "completed_accelerators":   ["[name1]", ...],
    "recommended_accelerators": ["[name1]", ...]
}
```

Then write this dict to a JSON file and invoke the CIP runner:

```bash
# Write data JSON
python3 -c "import json; open('/home/claude/cip_data.json','w').write(json.dumps(DATA_DICT, indent=2))"

# Run the hardened pipeline — handles unpack, edit, pack, validate in one pass
python3 /mnt/skills/user/cip-generator/cip_runner.py \
  --data /home/claude/cip_data.json \
  --output /home/claude/output_CIP_[ACCOUNT_NAME].pptx
```

The runner:
- Unpacks the master template
- Applies all slide edits from the data dict
- Packs using the skill-local patched pack.py (which normalizes OPC rels paths)
- DOES NOT run clean.py — clean.py deletes slides and must never be called
- Runs a full validation gate before returning
- Exits with a non-zero code and clear error messages on any failure

⚠️ NEVER run clean.py. It is incompatible with this template and will delete all slides.
⚠️ NEVER use /mnt/skills/public/pptx/scripts/office/pack.py — use the skill-local version
   at /mnt/skills/user/cip-generator/scripts/office/pack.py which has the OPC path fix.

---

### Step 6: Copy to Output and Deliver

The cip_runner.py validates the file before returning. If it exits cleanly, the file
is good. Copy to outputs and present:

```bash
cp /home/claude/output_CIP_[ACCOUNT_NAME].pptx \
   /mnt/user-data/outputs/CIP_[ACCOUNT_NAME].pptx
```

Call present_files with the output path.

Confirm to the user:
- Account name and CSM name populated
- Number of licensing rows filled
- Number of accelerators highlighted (completed + recommended)
- Any fields that returned N/A due to missing data

---

## Failure Handling

If Snowflake returns no data for the account:
- Confirm account number is correct with the user
- Retry with account name as the query parameter
- If still empty, populate all fields with N/A and flag to the user

If cip_runner.py exits with an error:
- Read the error message — it will identify which step failed
- Do not manually re-edit slides or re-pack — fix the data dict and re-run the runner
- The runner is idempotent — safe to re-run as many times as needed

If ValueMelody fails:
- Continue with Snowflake data only
- Set adoption_gaps to the best 4 from Snowflake licensed-but-not-deployed data
- Note in delivery message that ValueMelody data was unavailable

⚠️ If a "Failed to Load Document" error occurs after download:
- This is an OPC rels path issue — it means the wrong pack.py was used
- Re-run using /mnt/skills/user/cip-generator/scripts/office/pack.py (the patched version)
- Never use /mnt/skills/public/pptx/scripts/office/pack.py for CIP generation

---

## Slides Reference

| Slide | Auto-filled | Source |
|-------|------------|--------|
| 1 | Customer name, CSM name, year | Snowflake |
| 2 | Static | None |
| 3 | Static | None |
| 4 | All 13 Impact Reset fields | Snowflake + ValueMelody |
| 5 | Full licensing table | Snowflake |
| 6 | Initiative names, accelerator names, training credits (text only) | Snowflake |
| 7 | Static | None |
| 8 | Accelerator highlight fills (completed = green, recommended = blue) | Snowflake |
| 9-15 | Static | None |
