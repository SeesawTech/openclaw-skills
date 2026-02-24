---
name: seesaw
description: "Interact with SeeSaw Prediction Market — list markets, get quotes, buy/sell shares, check balance and positions."
metadata: {"openclaw":{"emoji":"🎯","always":true}}
---

# SeeSaw Prediction Market

## Configuration

Set the following environment variables:
- `SEESAW_BASE_URL`: API Base URL (default: `http://localhost:3000/v1`)
- `SEESAW_API_KEY`: Your API Key
- `SEESAW_API_SECRET`: Your API Secret

## Usage

All operations are handled by the `seesaw.py` script. 

> **Note:** Paths below assume execution from the repository root. If running from within the skill directory, use `python scripts/seesaw.py`.

### List Markets
```bash
python skills/seesaw/scripts/seesaw.py list-markets --status active --page 1 --limit 20
```

### Get Balance
```bash
python skills/seesaw/scripts/seesaw.py balance
```

### Get Quote
```bash
python skills/seesaw/scripts/seesaw.py quote <market_id> <option_uuid> <amount> --side buy
```

### Buy/Sell Shares
```bash
python skills/seesaw/scripts/seesaw.py buy <market_id> <option_uuid> <amount>
python skills/seesaw/scripts/seesaw.py sell <market_id> <option_uuid> <shares>
```

### Create Market
```bash
# 1. Upload image (optional)
python skills/seesaw/scripts/seesaw.py upload /path/to/image.jpg
# Returns {"file_url": "..."}

# 2. Create market
python skills/seesaw/scripts/seesaw.py create-market \
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
