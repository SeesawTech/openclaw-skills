#!/bin/bash
# github-watcher.sh - Poll GitHub notifications for Pull Requests needing attention.

# CONFIGURATION
# Set GITHUB_EXPECTED_ACCOUNT to verify the active account.
# Set WATCH_ORG (e.g. "SeesawTech") or WATCH_REPOS (comma-separated "owner/repo,owner2/repo2") to filter.
EXPECTED_ACCOUNT="${GITHUB_EXPECTED_ACCOUNT:-}"
WATCH_ORG="${WATCH_ORG:-}"
WATCH_REPOS="${WATCH_REPOS:-}"
STATE_FILE="/root/.openclaw/workspace/.github_watcher_state"

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
echo "Active GitHub account: $ACTIVE_ACCOUNT"

# Fetch PullRequest notifications
# filters for mentions, review_requested, and author (for updates)
NOTIFS_RAW=$(gh api notifications --jq '.[] | select(.subject.type == "PullRequest")')

if [ -z "$NOTIFS_RAW" ]; then
    echo "No new PullRequest notifications."
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

echo "Processing PullRequest notifications..."

FOUND_COUNT=0
echo "$NOTIFS" | while read -r notif; do
    ID=$(echo "$notif" | jq -r '.id')
    # Skip if already seen (simple id comparison assuming descending order)
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

    echo "Found PR: $REPO#$NUMBER ($REASON) - $TITLE"
    ((FOUND_COUNT++))

    # Guidance for the agent processing these notifications:
    # 1. review_requested: Review the PR.
    # 2. mention/author: Check for comments needing a reply.
    # Note: For programming tasks, use 'coding-agent' for implementation.

    if [ "$REASON" == "review_requested" ]; then
        echo "Action required: Review $REPO#$NUMBER"
    elif [ "$REASON" == "mention" ] || [ "$REASON" == "author" ]; then
        echo "Action required: Check comments and reply in $REPO#$NUMBER"
    fi
done

if [ "$FOUND_COUNT" -eq 0 ]; then
    echo "No new notifications matching filters."
fi
