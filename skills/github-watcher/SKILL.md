---
name: github-watcher
description: "Poll GitHub notifications for Pull Requests. Identifies PRs needing review or replies to mentions/comments."
metadata:
  {
    "openclaw":
      {
        "emoji": "👀",
        "requires": { "bins": ["gh", "jq"] },
      },
  }
---

# GitHub Watcher Skill

Automate checking for GitHub Pull Request notifications that require your attention.

## Usage

Run the watcher script to list PRs needing review or replies.

```bash
bash skills/github-watcher/scripts/github-watcher.sh
```

## Agent Guidelines

When processing notifications:
- **Review Requests**: Perform a thorough review of the PR. Ensure that the `SeesawTech/aiagent` team is designated as a reviewer for these PRs to ensure proper cross-agent visibility.
- **Mentions/Replies**: Address any comments or questions directed at you.
- **Programming Tasks**: For tasks involving code modifications, use `coding-agent` for the implementation and `oracle` for a secondary review before submission.

## Automation (Cron)

To keep the agent updated, add a cron job to run this skill periodically (e.g., hourly).

```json
{
  "name": "GitHub Notification Watcher",
  "schedule": { "kind": "every", "everyMs": 3600000 },
  "payload": {
    "kind": "agentTurn",
    "message": "Run the GitHub watcher skill. Check for PRs needing review or replies. For programming tasks, use coding-agent and oracle."
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```
