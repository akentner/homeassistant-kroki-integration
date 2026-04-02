#!/usr/bin/env bash
# Interactive release script for homeassistant-kroki-integration.
# Usage: ./scripts/release.sh  (or: make release)
set -euo pipefail

MANIFEST="custom_components/kroki/manifest.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

red()   { printf '\033[31m%s\033[0m\n' "$*"; }
green() { printf '\033[32m%s\033[0m\n' "$*"; }
cyan()  { printf '\033[36m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }

bump_version() {
    local version="$1" part="$2"
    local base major minor patch
    # Strip pre-release suffix (e.g. -alpha.1) before arithmetic
    base="${version%%-*}"
    IFS='.' read -r major minor patch <<< "$base"
    case "$part" in
        major) echo "$((major + 1)).0.0" ;;
        minor) echo "${major}.$((minor + 1)).0" ;;
        patch) echo "${major}.${minor}.$((patch + 1))" ;;
    esac
}

# ---------------------------------------------------------------------------
# 1. Sanity checks
# ---------------------------------------------------------------------------

if ! command -v gh &>/dev/null; then
    red "ERROR: 'gh' (GitHub CLI) is not installed or not on PATH."
    exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    red "ERROR: Working tree has uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Show current state
# ---------------------------------------------------------------------------

echo ""
bold "=== Kroki Integration Release ==="
echo ""

CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('${MANIFEST}'))['version'])")
cyan "Current manifest version : ${CURRENT_VERSION}"

LAST_RELEASE=$(gh release list --limit 1 --json tagName,publishedAt \
    --jq '.[0] | "\(.tagName)  (published \(.publishedAt | strptime("%Y-%m-%dT%H:%M:%SZ") | strftime("%Y-%m-%d")))"' 2>/dev/null \
    || echo "none")
cyan "Last GitHub release      : ${LAST_RELEASE}"
echo ""

# ---------------------------------------------------------------------------
# 3. Ask for new version
# ---------------------------------------------------------------------------

SUGGEST_PATCH=$(bump_version "$CURRENT_VERSION" patch)
SUGGEST_MINOR=$(bump_version "$CURRENT_VERSION" minor)
SUGGEST_MAJOR=$(bump_version "$CURRENT_VERSION" major)

echo "Suggested versions:"
echo "  [1] patch → ${SUGGEST_PATCH}"
echo "  [2] minor → ${SUGGEST_MINOR}"
echo "  [3] major → ${SUGGEST_MAJOR}"
echo "  [4] custom"
echo ""

read -rp "Choose [1/2/3/4]: " CHOICE
case "$CHOICE" in
    1) NEW_VERSION="$SUGGEST_PATCH" ;;
    2) NEW_VERSION="$SUGGEST_MINOR" ;;
    3) NEW_VERSION="$SUGGEST_MAJOR" ;;
    4)
        read -rp "Enter version (without 'v'): " NEW_VERSION
        if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-(alpha|beta|rc)(\.[0-9]+)?)?$ ]]; then
            red "ERROR: Invalid version format '${NEW_VERSION}'. Expected X.Y.Z or X.Y.Z-alpha.N / -beta.N / -rc.N"
            exit 1
        fi
        ;;
    *)
        red "Invalid choice."
        exit 1
        ;;
esac

echo ""
bold "New version: v${NEW_VERSION}"
echo ""

# ---------------------------------------------------------------------------
# 4. Update manifest.json
# ---------------------------------------------------------------------------

python3 - <<EOF
import json, pathlib
path = pathlib.Path("${MANIFEST}")
data = json.loads(path.read_text())
data["version"] = "${NEW_VERSION}"
path.write_text(json.dumps(data, indent=2) + "\n")
EOF

green "Updated ${MANIFEST} → version ${NEW_VERSION}"

# ---------------------------------------------------------------------------
# 5. Commit strategy: amend or new commit?
# ---------------------------------------------------------------------------

echo ""

# Check if HEAD is already on remote
LOCAL_SHA=$(git rev-parse HEAD)
REMOTE_SHA=$(git rev-parse "@{u}" 2>/dev/null || echo "")

if [[ "$LOCAL_SHA" == "$REMOTE_SHA" ]]; then
    # HEAD is already pushed → must be a new commit
    COMMIT_STRATEGY="new"
else
    # HEAD is ahead of remote → offer amend
    LAST_MSG=$(git log -1 --format="%s")
    echo "HEAD is not yet pushed."
    echo "Last commit message: \"${LAST_MSG}\""
    echo ""
    echo "  [1] Amend last commit (include version bump in existing commit)"
    echo "  [2] New commit       (separate 'Bump version to ${NEW_VERSION}' commit)"
    echo ""
    read -rp "Choose [1/2]: " COMMIT_CHOICE
    case "$COMMIT_CHOICE" in
        1) COMMIT_STRATEGY="amend" ;;
        2) COMMIT_STRATEGY="new" ;;
        *)
            red "Invalid choice."
            git checkout -- "$MANIFEST"
            exit 1
            ;;
    esac
fi

echo ""
git add "$MANIFEST"

if [[ "$COMMIT_STRATEGY" == "amend" ]]; then
    git commit --amend --no-edit
    green "Amended last commit with version bump."
else
    git commit -m "Bump version to ${NEW_VERSION}"
    green "Created new commit: Bump version to ${NEW_VERSION}"
fi

# ---------------------------------------------------------------------------
# 6. Push
# ---------------------------------------------------------------------------

echo ""
if [[ "$COMMIT_STRATEGY" == "amend" ]]; then
    read -rp "Push with --force-with-lease? [y/N]: " PUSH_CONFIRM
    if [[ "$PUSH_CONFIRM" =~ ^[Yy]$ ]]; then
        git push --force-with-lease
        green "Force-pushed."
    else
        red "Aborted. Don't forget to push manually."
        exit 1
    fi
else
    git push
    green "Pushed."
fi

# ---------------------------------------------------------------------------
# 7. Create GitHub release
# ---------------------------------------------------------------------------

echo ""
read -rp "Enter release notes (leave empty to auto-generate from commits): " RELEASE_NOTES
echo ""

TAG="v${NEW_VERSION}"

# Mark as pre-release if version contains a pre-release suffix
PRERELEASE_FLAG=""
if [[ "$NEW_VERSION" =~ -(alpha|beta|rc) ]]; then
    PRERELEASE_FLAG="--prerelease"
fi

if [[ -z "$RELEASE_NOTES" ]]; then
    gh release create "$TAG" \
        --title "$TAG" \
        --generate-notes \
        $PRERELEASE_FLAG
else
    gh release create "$TAG" \
        --title "$TAG" \
        --notes "$RELEASE_NOTES" \
        $PRERELEASE_FLAG
fi

echo ""
green "Release ${TAG} created!"
gh release view "$TAG" --json url --jq '.url'
echo ""
