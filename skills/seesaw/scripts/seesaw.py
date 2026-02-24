import os
import json
import requests
import argparse
import sys
from datetime import datetime

TOKEN_CACHE = "/tmp/seesaw_token.json"

class SeesawClient:
    def __init__(self, base_url=None, api_key=None, api_secret=None):
        self.base_url = base_url or os.getenv("SEESAW_BASE_URL", "http://localhost:3000/v1")
        self.api_key = api_key or os.getenv("SEESAW_API_KEY")
        self.api_secret = api_secret or os.getenv("SEESAW_API_SECRET")
        self.token = self._load_token()

    def _load_token(self):
        if os.path.exists(TOKEN_CACHE):
            try:
                with open(TOKEN_CACHE, 'r') as f:
                    data = json.load(f)
                    return data.get("token")
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def _save_token(self, token):
        self.token = token
        try:
            with open(TOKEN_CACHE, 'w') as f:
                json.dump({"token": token}, f)
        except IOError:
            pass

    def login(self):
        if not self.api_key or not self.api_secret:
            raise ValueError("SEESAW_API_KEY and SEESAW_API_SECRET must be set")
        
        url = f"{self.base_url}/auth/agent-login"
        payload = {"api_key": self.api_key, "api_secret": self.api_secret}
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Login failed: {e}")
        
        token = resp.json().get("token")
        self._save_token(token)
        return token

    def _request(self, method, path, **kwargs):
        if not self.token:
            self.login()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        kwargs["headers"] = headers
        if "timeout" not in kwargs:
            kwargs["timeout"] = 15
        
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = requests.request(method, url, **kwargs)
            
            if resp.status_code == 401:
                self.login()
                headers["Authorization"] = f"Bearer {self.token}"
                resp = requests.request(method, url, **kwargs)
                
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request to {path} failed: {e}")

    def list_markets(self, page=1, limit=20, status="active", category_id=None):
        params = {"page": page, "limit": limit, "status": status}
        if category_id:
            params["category_id"] = category_id
        return self._request("GET", "markets", params=params)

    def get_market(self, market_id):
        return self._request("GET", f"markets/{market_id}")

    def get_quote(self, market_id, option_id, amount, side="buy"):
        params = {
            "prediction_id": market_id,
            "option_id": option_id,
            "amount": amount,
            "side": side
        }
        return self._request("GET", "trade/quote", params=params)

    def buy(self, market_id, option_id, amount):
        payload = {
            "prediction_id": market_id,
            "option_id": option_id,
            "amount": str(amount)
        }
        return self._request("POST", "trade/buy", json=payload)

    def sell(self, market_id, option_id, shares):
        payload = {
            "prediction_id": market_id,
            "option_id": option_id,
            "shares": str(shares)
        }
        return self._request("POST", "trade/sell", json=payload)

    def get_positions(self, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", "trade/positions", params=params)

    def get_balance(self):
        return self._request("GET", "wallet/balance")

    def get_presigned_url(self, content_type="image/jpeg", file_extension="jpg"):
        params = {"content_type": content_type, "file_extension": file_extension}
        return self._request("GET", "upload/presigned-url", params=params)

    def upload_file(self, upload_url, file_path, content_type):
        with open(file_path, 'rb') as f:
            resp = requests.put(upload_url, data=f, headers={"Content-Type": content_type})
            resp.raise_for_status()
        return True

    def create_market(self, title, options, end_time, description=None, initial_probabilities=None, image_urls=None):
        payload = {
            "title": title,
            "options": options,
            "end_time": end_time
        }
        if description: payload["description"] = description
        if initial_probabilities: payload["initial_probabilities"] = initial_probabilities
        if image_urls: payload["image_urls"] = image_urls
        return self._request("POST", "markets", json=payload)

def main():
    parser = argparse.ArgumentParser(description="SeeSaw Prediction Market CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Balance
    subparsers.add_parser("balance", help="Get wallet balance")

    # Markets
    p_list = subparsers.add_parser("list-markets", help="List prediction markets")
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--status", default="active")
    p_list.add_argument("--category", dest="category_id")

    p_get = subparsers.add_parser("get-market", help="Get market details")
    p_get.add_argument("id", help="Market ID")

    # Trade
    p_quote = subparsers.add_parser("quote", help="Get a quote")
    p_quote.add_argument("market_id")
    p_quote.add_argument("option_id")
    p_quote.add_argument("amount", type=int)
    p_quote.add_argument("--side", choices=["buy", "sell"], default="buy")

    p_buy = subparsers.add_parser("buy", help="Buy shares")
    p_buy.add_argument("market_id")
    p_buy.add_argument("option_id")
    p_buy.add_argument("amount", type=int)

    p_sell = subparsers.add_parser("sell", help="Sell shares")
    p_sell.add_argument("market_id")
    p_sell.add_argument("option_id")
    p_sell.add_argument("shares", type=int)

    subparsers.add_parser("positions", help="Get positions")

    # Creation
    p_create = subparsers.add_parser("create-market", help="Create a new market")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--options", nargs="+", required=True)
    p_create.add_argument("--end-time", required=True, help="ISO8601 string")
    p_create.add_argument("--description")
    p_create.add_argument("--probs", type=int, nargs="+", help="Initial probabilities")
    p_create.add_argument("--images", nargs="+", help="Image URLs")

    p_upload = subparsers.add_parser("upload", help="Upload an image")
    p_upload.add_argument("file", help="Path to image file")
    p_upload.add_argument("--type", default="image/jpeg")
    p_upload.add_argument("--ext", default="jpg")

    args = parser.parse_args()
    client = SeesawClient()

    try:
        if args.command == "balance":
            print(json.dumps(client.get_balance(), indent=2))
        elif args.command == "list-markets":
            print(json.dumps(client.list_markets(args.page, args.limit, args.status, args.category_id), indent=2))
        elif args.command == "get-market":
            print(json.dumps(client.get_market(args.id), indent=2))
        elif args.command == "quote":
            print(json.dumps(client.get_quote(args.market_id, args.option_id, args.amount, args.side), indent=2))
        elif args.command == "buy":
            print(json.dumps(client.buy(args.market_id, args.option_id, args.amount), indent=2))
        elif args.command == "sell":
            print(json.dumps(client.sell(args.market_id, args.option_id, args.shares), indent=2))
        elif args.command == "positions":
            print(json.dumps(client.get_positions(), indent=2))
        elif args.command == "create-market":
            if args.probs and len(args.probs) != len(args.options):
                print(f"Error: Number of initial probabilities ({len(args.probs)}) must match number of options ({len(args.options)})", file=sys.stderr)
                sys.exit(1)
            print(json.dumps(client.create_market(args.title, args.options, args.end_time, args.description, args.probs, args.images), indent=2))
        elif args.command == "upload":
            presigned = client.get_presigned_url(args.type, args.ext)
            client.upload_file(presigned["upload_url"], args.file, args.type)
            print(json.dumps({"file_url": presigned["file_url"]}, indent=2))
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
