---
name: seesaw-agent
description: "Interact with SeeSaw Prediction Market — list markets, get quotes, buy/sell shares, check balance and positions."
metadata: {"openclaw":{"emoji":"🎯","always":true}}
---

# SeeSaw Prediction Market

## Configuration

These variables are managed via the OpenClaw Gateway Config (`openclaw.json`) under `env.vars`. The `seesaw.py` script automatically reads them from the environment:

- `SEESAW_BASE_URL`: API Base URL (e.g., `https://app.seesaw.fun/v1`)
- `SEESAW_API_KEY`: Your API Key
- `SEESAW_API_SECRET`: Your API Secret

To update these, use the `gateway config.patch` tool or edit `openclaw.json` directly.

## Usage

All operations are handled by the `seesaw.py` script. 

> **Note:** Paths below assume execution from the repository root.

### Wallet
```bash
python skills/seesaw-agent/scripts/seesaw.py balance
python skills/seesaw-agent/scripts/seesaw.py transactions --page 1 --limit 20
python skills/seesaw-agent/scripts/seesaw.py credit-history
python skills/seesaw-agent/scripts/seesaw.py daily-gift-status
python skills/seesaw-agent/scripts/seesaw.py claim-daily-gift
```

### Markets
```bash
python skills/seesaw-agent/scripts/seesaw.py list-markets --status active --page 1 --limit 20
python skills/seesaw-agent/scripts/seesaw.py get-market <market_id>
python skills/seesaw-agent/scripts/seesaw.py market-activity <market_id>
python skills/seesaw-agent/scripts/seesaw.py price-history <market_id>
python skills/seesaw-agent/scripts/seesaw.py holders <market_id>
python skills/seesaw-agent/scripts/seesaw.py traders <market_id>
```

### Trade
```bash
python skills/seesaw-agent/scripts/seesaw.py quote <market_id> <option_uuid> <amount> --side buy
python skills/seesaw-agent/scripts/seesaw.py buy <market_id> <option_uuid> <amount>
python skills/seesaw-agent/scripts/seesaw.py sell <market_id> <option_uuid> <shares>
python skills/seesaw-agent/scripts/seesaw.py positions
python skills/seesaw-agent/scripts/seesaw.py trade-history
```

### User & Social
```bash
python skills/seesaw-agent/scripts/seesaw.py profile <user_id>
python skills/seesaw-agent/scripts/seesaw.py leaderboard
python skills/seesaw-agent/scripts/seesaw.py followers <user_id>
python skills/seesaw-agent/scripts/seesaw.py following <user_id>
python skills/seesaw-agent/scripts/seesaw.py favorites <user_id>
python skills/seesaw-agent/scripts/seesaw.py follow <user_id>
python skills/seesaw-agent/scripts/seesaw.py unfollow <user_id>
python skills/seesaw-agent/scripts/seesaw.py block <user_id>
python skills/seesaw-agent/scripts/seesaw.py unblock <user_id>
```

### Comments
```bash
python skills/seesaw-agent/scripts/seesaw.py comments <market_id>
python skills/seesaw-agent/scripts/seesaw.py add-comment <market_id> "content here"
python skills/seesaw-agent/scripts/seesaw.py delete-comment <market_id> <comment_id>
python skills/seesaw-agent/scripts/seesaw.py favorite <market_id>
python skills/seesaw-agent/scripts/seesaw.py unfavorite <market_id>
```

### Challenges
```bash
python skills/seesaw-agent/scripts/seesaw.py challenges
python skills/seesaw-agent/scripts/seesaw.py claim-challenge <challenge_id>
```

### Oracle
```bash
python skills/seesaw-agent/scripts/seesaw.py oracle-status <prediction_id>
python skills/seesaw-agent/scripts/seesaw.py assert <prediction_id> <option_id>
python skills/seesaw-agent/scripts/seesaw.py dispute <prediction_id> <option_id>
python skills/seesaw-agent/scripts/seesaw.py vote <prediction_id> <option_id>
python skills/seesaw-agent/scripts/seesaw.py settle <prediction_id>
```

### Categories
```bash
python skills/seesaw-agent/scripts/seesaw.py categories
```

### Create Market
```bash
# 1. Upload image (optional)
python skills/seesaw-agent/scripts/seesaw.py upload /path/to/image.jpg
# Returns {"file_url": "..."}

# 2. Create market
python skills/seesaw-agent/scripts/seesaw.py create-market \
  --title "Will X happen?" \
  --options "Yes" "No" \
  --end-time "2026-12-31T23:59:59Z" \
  --images "https://cdn.example.com/uploads/abc123.jpg"
```

## Setup

Ensure `requests` is installed:
```bash
pip install requests
```

## API Coverage

| Category | Endpoints |
|----------|-----------|
| **Wallet** | balance, transactions, credit-history, daily-gift |
| **Markets** | list, get, activity, price-history, holders, traders |
| **Trade** | quote, buy, sell, positions, history |
| **User** | profile, leaderboard, followers, following, favorites |
| **Social** | follow, unfollow, block, unblock, comments, favorite |
| **Challenges** | list, claim |
| **Oracle** | status, assert, dispute, vote, settle |
| **Categories** | list |
