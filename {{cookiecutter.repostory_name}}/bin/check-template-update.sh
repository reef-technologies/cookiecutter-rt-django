#!/bin/bash
# Report how many template commits this project is behind (see "Template updates" in AGENTS.md).
#
# Prints a single line when the template has commits that change generated projects
# and that are not applied here yet; prints nothing when the project is up to date
# or the check cannot be done (no .cruft.json, no network, unknown commit, ...).
# Always exits 0, so it never blocks the caller.

cd "$(dirname "$0")/.." || exit 0

[ -f .cruft.json ] || exit 0
command -v git >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

CRUFT_FIELDS=$(python3 -c '
import json
with open(".cruft.json") as f:
    cfg = json.load(f)
for key in ("template", "commit", "checkout", "directory"):
    print(cfg.get(key) or "")
' 2>/dev/null) || exit 0
{
  read -r TEMPLATE_URL
  read -r PROJECT_COMMIT
  read -r TEMPLATE_CHECKOUT
  read -r TEMPLATE_DIRECTORY
} <<<"$CRUFT_FIELDS"
[ -n "$TEMPLATE_URL" ] && [ -n "$PROJECT_COMMIT" ] || exit 0

TMPDIR_PATH=$(mktemp -d 2>/dev/null) || exit 0
trap 'rm -rf "$TMPDIR_PATH"' EXIT
CLONE_DIR="$TMPDIR_PATH/template.git"

with_timeout() {
  if command -v timeout >/dev/null 2>&1; then
    timeout "$@"
  else
    shift
    "$@"
  fi
}

# Fetch history only (no file contents); never prompt for credentials and give up on a stalled network.
GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" \
  with_timeout 20 git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=10 \
  clone --quiet --bare --filter=blob:none "$TEMPLATE_URL" "$CLONE_DIR" >/dev/null 2>&1 || exit 0

template_git() {
  git --git-dir="$CLONE_DIR" "$@"
}

TIP_COMMIT=$(template_git rev-parse --verify --quiet "${TEMPLATE_CHECKOUT:-HEAD}^{commit}") || exit 0
template_git cat-file -e "$PROJECT_COMMIT^{commit}" 2>/dev/null || exit 0

# Only count commits touching what ends up in a generated project:
# the project subtree (`{{cookiecutter.*}}` directory), generation hooks and cookiecutter.json.
TEMPLATE_ROOT=${TEMPLATE_DIRECTORY:+$TEMPLATE_DIRECTORY/}
PATHS=("${TEMPLATE_ROOT}hooks" "${TEMPLATE_ROOT}cookiecutter.json")
while IFS= read -r entry; do
  case "$entry" in
    "{{cookiecutter."*) PATHS+=("${TEMPLATE_ROOT}${entry}") ;;
  esac
done < <(template_git ls-tree --name-only "$TIP_COMMIT:$TEMPLATE_DIRECTORY" 2>/dev/null)

BEHIND=$(template_git rev-list --count "$PROJECT_COMMIT..$TIP_COMMIT" -- "${PATHS[@]}" 2>/dev/null) || exit 0
[ "$BEHIND" -gt 0 ] 2>/dev/null || exit 0

TEMPLATE_NAME=$(basename "${TEMPLATE_URL%/}" .git)
SYNCED_ON=$(template_git show --no-patch --format=%cs "$PROJECT_COMMIT" 2>/dev/null)
MESSAGE="This project is $BEHIND commits behind the $TEMPLATE_NAME template ($TEMPLATE_URL; last synced to a template commit from $SYNCED_ON)."

# Best effort: point to the open PR created by the weekly cruft update workflow.
if command -v gh >/dev/null 2>&1; then
  UPDATE_PR=$(GH_PROMPT_DISABLED=1 with_timeout 10 gh pr list --head cruft/update --state open \
    --json url --jq '.[0].url // empty' 2>/dev/null)
  if [ -n "$UPDATE_PR" ]; then
    MESSAGE="$MESSAGE Open template update PR: $UPDATE_PR"
  fi
fi

echo "$MESSAGE"
exit 0
