#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$HOME/repos/claude-artifacts"
STAGED_HTML="/tmp/artifact.html"

usage() {
  cat <<USAGE
Usage:
  $0 <folder-name> --update [--message "msg"]
  $0 <folder-name> --new --entry <path-to-entry.json> [--message "msg"]

Expects staged HTML at $STAGED_HTML
USAGE
  exit 1
}

[[ $# -lt 2 ]] && usage
[[ ! -f "$STAGED_HTML" ]] && { echo "ERROR: No staged HTML at $STAGED_HTML" >&2; exit 1; }

FOLDER="$1"
MODE="$2"
shift 2

ENTRY_FILE=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --entry) ENTRY_FILE="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    *) echo "ERROR: unknown arg: $1" >&2; usage ;;
  esac
done

if [[ "$MODE" == "--new" ]]; then
  [[ -z "$ENTRY_FILE" ]] && { echo "ERROR: --new requires --entry <path>" >&2; usage; }
  [[ ! -f "$ENTRY_FILE" ]] && { echo "ERROR: entry file not found: $ENTRY_FILE" >&2; exit 1; }
elif [[ "$MODE" != "--update" ]]; then
  echo "ERROR: mode must be --new or --update" >&2
  usage
fi

[[ -z "$MESSAGE" ]] && MESSAGE="deploy: $FOLDER"

cd "$REPO_DIR"

echo "Pulling latest from origin/main..."
git pull origin main --quiet || { echo "ERROR: git pull failed" >&2; exit 1; }

if [[ -f "$FOLDER/index.html" && "$MODE" == "--new" ]]; then
  echo "ERROR: $FOLDER/index.html already exists. Use --update." >&2
  exit 1
fi
if [[ ! -f "$FOLDER/index.html" && "$MODE" == "--update" ]]; then
  echo "ERROR: $FOLDER/index.html does not exist. Use --new." >&2
  exit 1
fi

mkdir -p "$FOLDER"
cp "$STAGED_HTML" "$FOLDER/index.html"
echo "Wrote $FOLDER/index.html ($(wc -c < "$FOLDER/index.html") bytes)"

if [[ "$MODE" == "--new" ]]; then
  node - "$ENTRY_FILE" "artifacts.json" <<'NODE_EOF'
const fs = require('fs');
const [,, entryPath, registryPath] = process.argv;
const entry = JSON.parse(fs.readFileSync(entryPath, 'utf8'));
const data = JSON.parse(fs.readFileSync(registryPath, 'utf8'));

if (Array.isArray(data)) {
  data.push(entry);
} else if (data.artifacts && Array.isArray(data.artifacts)) {
  data.artifacts.push(entry);
} else {
  console.error('ERROR: artifacts.json structure not recognized (expected array or { artifacts: [...] })');
  process.exit(1);
}

fs.writeFileSync(registryPath, JSON.stringify(data, null, 2) + '\n');
NODE_EOF
  echo "Updated artifacts.json"
fi

git add -A
if git diff --cached --quiet; then
  echo "No changes to commit. Already deployed?"
  echo ""
  echo "URL: https://ceg-csp.github.io/claude-artifacts/$FOLDER/"
  exit 0
fi

git commit -m "$MESSAGE" --quiet
git push origin main --quiet
echo "Pushed"
echo ""
echo "Deploy complete"
echo ""
echo "Folder:    $FOLDER"
echo "Path:      $FOLDER/index.html"
echo "URL:       https://ceg-csp.github.io/claude-artifacts/$FOLDER/"
echo "Library:   https://ceg-csp.github.io/claude-artifacts/"
echo ""
echo "Note: GitHub Pages may take 1-2 min to reflect changes."
