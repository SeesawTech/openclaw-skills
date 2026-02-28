#!/bin/bash
# github-watcher.sh - Poll GitHub notifications for Pull Requests needing attention.

# CONFIGURATION
# Set GITHUB_EXPECTED_ACCOUNT to verify the active account.
# Set WATCH_ORG (e.g. "SeesawTech") or WATCH_REPOS (comma-separated "owner/repo,owner2/repo2") to filter.
EXPECTED_ACCOUNT="${GITHUB_EXPECTED_ACCOUNT:-}"
WATCH_ORG="${WATCH_ORG:-}"
WATCH_REPOS="${WATCH_REPOS:-}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}"
STATE_FILE="$STATE_DIR/github_watcher_state"
mkdir -p "$STATE_DIR"

# Ensure gh CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: gh CLI not authenticated."
    exit 1
fi

# Account Validation
ACTIVE_ACCOUNT=$(gh api user --jq '.login')
if [ -n "$EXPECTED_ACCOUNT" ] && [ "$ACTIVE_ACCOUNT" != "$EXPECTED_ACCOUNT" ]; then
    echo "Error: gh active account ($ACTIVE_ACCOUNT) does not match GITHUB_EXPECTED_ACCOUNT ($EXPECTED_ACCOUNT)."
    exit 1
fi

# Fetch PullRequest notifications
# filters for mentions, review_requested, and author (for updates)
NOTIFS_RAW=$(gh api notifications --jq '.[] | select(.subject.type == "PullRequest")')

if [ -z "$NOTIFS_RAW" ]; then
    # SILENT_IF_EMPTY=true (handled by agent or via NO_REPLY)
    exit 0
fi

# Load state
LAST_ID=""
if [ -f "$STATE_FILE" ]; then
    LAST_ID=$(cat "$STATE_FILE")
fi

NEW_LAST_ID=$(echo "$NOTIFS_RAW" | jq -r '.id' | head -n 1)
[ -n "$NEW_LAST_ID" ] && echo "$NEW_LAST_ID" > "$STATE_FILE"

NOTIFS=$(echo "$NOTIFS_RAW" | jq -c ". | {id: .id, repo: .repository.full_name, org: .repository.owner.login, title: .subject.title, reason: .reason, url: .subject.url, number: (.subject.url | split(\"/\") | last)}")

FOUND_COUNT=0
OUTPUT=""

while read -r notif; do
    ID=$(echo "$notif" | jq -r '.id')
    # Skip if already seen
    if [ -n "$LAST_ID" ] && [ "$ID" == "$LAST_ID" ]; then
        break
    fi

    REPO=$(echo "$notif" | jq -r '.repo')
    ORG=$(echo "$notif" | jq -r '.org')
    
    # Org/Repo Filters
    if [ -n "$WATCH_ORG" ] && [ "$ORG" != "$WATCH_ORG" ]; then continue; fi
    if [ -n "$WATCH_REPOS" ] && [[ ! ",$WATCH_REPOS," =~ ",$REPO," ]]; then continue; fi

    NUMBER=$(echo "$notif" | jq -r '.number')
    REASON=$(echo "$notif" | jq -r '.reason')
    TITLE=$(echo "$notif" | jq -r '.title')

    LINE="Found PR: $REPO#$NUMBER ($REASON) - $TITLE"
    OUTPUT="$OUTPUT$LINE\n"
    ((FOUND_COUNT++))

    if [ "$REASON" == "review_requested" ]; then
        OUTPUT="${OUTPUT}Action required: Review $REPO#$NUMBER\n"
    elif [ "$REASON" == "mention" ] || [ "$REASON" == "author" ]; then
        OUTPUT="${OUTPUT}Action required: Check comments and reply in $REPO#$NUMBER\n"
    fi
done <<< "$NOTIFS"

if [ "$FOUND_COUNT" -gt 0 ]; then
    echo "Processing PullRequest notifications..."
    echo -e "$OUTPUT"
fi
