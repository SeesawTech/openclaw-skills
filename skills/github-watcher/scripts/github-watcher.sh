#!/bin/bash
# github-watcher.sh - Poll GitHub notifications for Pull Requests needing attention.

# Ensure gh CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: gh CLI not authenticated."
    exit 1
fi

# Fetch PullRequest notifications
# filters for mentions, review_requested, and author (for updates)
NOTIFS=$(gh api notifications --jq '.[] | select(.subject.type == "PullRequest") | {repo: .repository.full_name, title: .subject.title, reason: .reason, url: .subject.url, number: (.subject.url | split("/") | last)}')

if [ -z "$NOTIFS" ]; then
    echo "No new PullRequest notifications."
    exit 0
fi

echo "Processing PullRequest notifications..."

echo "$NOTIFS" | jq -c '.' | while read -r notif; do
    REPO=$(echo "$notif" | jq -r '.repo')
    NUMBER=$(echo "$notif" | jq -r '.number')
    REASON=$(echo "$notif" | jq -r '.reason')
    TITLE=$(echo "$notif" | jq -r '.title')

    echo "Found PR: $REPO#$NUMBER ($REASON) - $TITLE"

    # Guidance for the agent processing these notifications:
    # 1. review_requested: Review the PR.
    # 2. mention/author: Check for comments needing a reply.
    # Note: For programming tasks, use 'coding-agent' for implementation and 'oracle' for review.

    if [ "$REASON" == "review_requested" ]; then
        echo "Action required: Review $REPO#$NUMBER"
        echo "Note: Ensure 'SeesawTech/aiagent' team is requested for review if applicable."
    elif [ "$REASON" == "mention" ] || [ "$REASON" == "author" ]; then
        echo "Action required: Check comments and reply in $REPO#$NUMBER"
    fi
done
