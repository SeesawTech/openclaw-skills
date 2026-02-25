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
# Optional configuration
export GITHUB_EXPECTED_ACCOUNT="my-agent-account"
export WATCH_ORG="SeesawTech"

bash skills/github-watcher/scripts/github-watcher.sh
```

### Configuration Variables
- `GITHUB_EXPECTED_ACCOUNT`: If set, script fails if `gh` is authenticated as a different user.
- `WATCH_ORG`: Filter notifications to a specific organization.
- `WATCH_REPOS`: Comma-separated list of `owner/repo` to watch (e.g. `SeesawTech/openclaw-skills,SeesawTech/app-prototype`).

## Agent Guidelines

When processing notifications:
- **Review Requests**: Perform a thorough review of the PR.
- **Mentions/Replies**: Address any comments or questions directed at you.
- **Programming Tasks**: For tasks involving code modifications, use `coding-agent` for the implementation.

## Automation (Cron)

To keep the agent updated, add a cron job to run this skill periodically (e.g., hourly).

```json
{
  "name": "GitHub Notification Watcher",
  "schedule": { "kind": "every", "everyMs": 3600000 },
  "payload": {
    "kind": "agentTurn",
    "message": "Run the GitHub watcher skill. Check for PRs needing review or replies. For programming tasks, use coding-agent. IMPORTANT: If there are no new notifications or actions to take, respond with ONLY: NO_REPLY (remain silent)."
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```
