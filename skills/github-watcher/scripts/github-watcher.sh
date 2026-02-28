#!/bin/bash
# github-watcher.sh - Poll GitHub notifications for Pull Requests needing attention.
# Maintains local state to only report NEW activity.

# Define state file path
STATE_FILE="memory/github-watcher-state.json"
mkdir -p "$(dirname "$STATE_FILE")"

# Ensure gh CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: gh CLI not authenticated."
    exit 1
fi

# Fetch current notifications for PullRequests
CURRENT_NOTIFS=$(gh api notifications --jq '.[] | select(.subject.type == "PullRequest") | {id: .id, repo: .repository.full_name, title: .subject.title, reason: .reason, url: .subject.url, number: (.subject.url | split("/") | last)}' | jq -s '.')

if [ "$CURRENT_NOTIFS" == "[]" ] || [ -z "$CURRENT_NOTIFS" ]; then
    echo "[]" > "$STATE_FILE"
    exit 0
fi

# Load previous state
if [ -f "$STATE_FILE" ]; then
    PREV_NOTIFS=$(cat "$STATE_FILE")
else
    PREV_NOTIFS="[]"
fi

# Identify NEW notifications
NEW_NOTIFS=$(jq -n --argjson curr "$CURRENT_NOTIFS" --argjson prev "$PREV_NOTIFS" \
    '$curr | map(select(. as $c | ($prev | map(.id) | contains([$c.id]) | not)))')

# Save current state
echo "$CURRENT_NOTIFS" > "$STATE_FILE"

if [ "$NEW_NOTIFS" == "[]" ] || [ -z "$NEW_NOTIFS" ]; then
    # No NEW activity
    exit 0
fi

echo "Processing NEW PullRequest notifications..."

echo "$NEW_NOTIFS" | jq -c '.[]' | while read -r notif; do
    REPO=$(echo "$notif" | jq -r '.repo')
    NUMBER=$(echo "$notif" | jq -r '.number')
    REASON=$(echo "$notif" | jq -r '.reason')
    TITLE=$(echo "$notif" | jq -r '.title')

    echo "Found NEW PR activity: $REPO#$NUMBER ($REASON) - $TITLE"

    if [ "$REASON" == "review_requested" ]; then
        echo "Action required: Review $REPO#$NUMBER"
        echo "Note: Ensure 'SeesawTech/aiagent' team is requested for review if applicable."
    elif [ "$REASON" == "mention" ] || [ "$REASON" == "author" ]; then
        echo "Action required: Check comments and reply in $REPO#$NUMBER"
    fi
done
