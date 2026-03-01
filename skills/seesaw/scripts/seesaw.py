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

    # ========== MARKETS ==========
    def list_markets(self, page=1, limit=20, status="active", category_id=None):
        params = {"page": page, "limit": limit, "status": status}
        if category_id:
            params["category_id"] = category_id
        return self._request("GET", "markets", params=params)

    def get_market(self, market_id):
        return self._request("GET", f"markets/{market_id}")

    def get_market_activity(self, market_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"markets/{market_id}/activity", params=params)

    def get_price_history(self, market_id):
        return self._request("GET", f"markets/{market_id}/price-history")

    def get_holders(self, market_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"markets/{market_id}/holders", params=params)

    def get_traders(self, market_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"markets/{market_id}/traders", params=params)

    # ========== TRADE ==========
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

    def get_trade_history(self, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", "trade/history", params=params)

    # ========== WALLET ==========
    def get_balance(self):
        return self._request("GET", "wallet/balance")

    def get_transactions(self, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", "wallet/transactions", params=params)

    def get_credit_history(self, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", "wallet/credit-history", params=params)

    def get_daily_gift_status(self):
        return self._request("GET", "wallet/daily-gift")

    def claim_daily_gift(self):
        return self._request("POST", "wallet/daily-gift")

    # ========== USER ==========
    def get_profile(self, user_id):
        return self._request("GET", f"users/{user_id}")

    def get_default_avatars(self):
        return self._request("GET", "users/default-avatars")

    def get_leaderboard(self, page=1, limit=20, timeframe="all"):
        params = {"page": page, "limit": limit, "timeframe": timeframe}
        return self._request("GET", "users/leaderboard", params=params)

    def get_followers(self, user_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"users/{user_id}/followers", params=params)

    def get_following(self, user_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"users/{user_id}/following", params=params)

    def get_favorites(self, user_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"users/{user_id}/favorites", params=params)

    def follow(self, user_id):
        return self._request("POST", f"users/{user_id}/follow")

    def unfollow(self, user_id):
        return self._request("DELETE", f"users/{user_id}/follow")

    def block(self, user_id):
        return self._request("POST", f"users/{user_id}/block")

    def unblock(self, user_id):
        return self._request("DELETE", f"users/{user_id}/block")

    # ========== SOCIAL ==========
    def get_comments(self, market_id, page=1, limit=20):
        params = {"page": page, "limit": limit}
        return self._request("GET", f"markets/{market_id}/comments", params=params)

    def add_comment(self, market_id, content):
        payload = {"content": content}
        return self._request("POST", f"markets/{market_id}/comments", json=payload)

    def delete_comment(self, market_id, comment_id):
        return self._request("DELETE", f"markets/{market_id}/comments/{comment_id}")

    def favorite(self, market_id):
        return self._request("POST", f"markets/{market_id}/favorite")

    def unfavorite(self, market_id):
        return self._request("DELETE", f"markets/{market_id}/favorite")

    # ========== CHALLENGES ==========
    def list_challenges(self):
        return self._request("GET", "challenges")

    def claim_challenge(self, challenge_id):
        return self._request("POST", f"challenges/{challenge_id}/claim")

    # ========== ORACLE ==========
    def get_oracle_status(self, prediction_id):
        return self._request("GET", f"oracle/status/{prediction_id}")

    def assert_result(self, prediction_id, option_id):
        payload = {"prediction_id": prediction_id, "option_id": option_id}
        return self._request("POST", "oracle/assert", json=payload)

    def dispute_result(self, prediction_id, option_id):
        payload = {"prediction_id": prediction_id, "option_id": option_id}
        return self._request("POST", "oracle/dispute", json=payload)

    def vote(self, prediction_id, option_id):
        payload = {"prediction_id": prediction_id, "option_id": option_id}
        return self._request("POST", "oracle/vote", json=payload)

    def settle(self, prediction_id):
        return self._request("POST", f"oracle/settle", json={"prediction_id": prediction_id})

    # ========== CATEGORIES ==========
    def list_categories(self):
        return self._request("GET", "categories")

    # ========== UPLOAD ==========
    def get_presigned_url(self, content_type="image/jpeg", file_extension="jpg"):
        params = {"content_type": content_type, "file_extension": file_extension}
        return self._request("GET", "upload/presigned-url", params=params)

    def upload_file(self, upload_url, file_path, content_type):
        with open(file_path, 'rb') as f:
            resp = requests.put(upload_url, data=f, headers={"Content-Type": content_type})
            resp.raise_for_status()
        return True

    # ========== MARKET CREATION ==========
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

    # ========== WALLET ==========
    subparsers.add_parser("balance", help="Get wallet balance")
    
    p_tx = subparsers.add_parser("transactions", help="Get transaction history")
    p_tx.add_argument("--page", type=int, default=1)
    p_tx.add_argument("--limit", type=int, default=20)

    p_credit = subparsers.add_parser("credit-history", help="Get credit history")
    p_credit.add_argument("--page", type=int, default=1)
    p_credit.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("daily-gift-status", help="Get daily gift status")
    subparsers.add_parser("claim-daily-gift", help="Claim daily gift")

    # ========== MARKETS ==========
    p_list = subparsers.add_parser("list-markets", help="List prediction markets")
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--status", default="active")
    p_list.add_argument("--category", dest="category_id")

    p_get = subparsers.add_parser("get-market", help="Get market details")
    p_get.add_argument("id", help="Market ID")

    p_activity = subparsers.add_parser("market-activity", help="Get market activity")
    p_activity.add_argument("market_id")
    p_activity.add_argument("--page", type=int, default=1)
    p_activity.add_argument("--limit", type=int, default=20)

    p_price = subparsers.add_parser("price-history", help="Get price history")
    p_price.add_argument("market_id")

    p_holders = subparsers.add_parser("holders", help="Get market holders")
    p_holders.add_argument("market_id")
    p_holders.add_argument("--page", type=int, default=1)
    p_holders.add_argument("--limit", type=int, default=20)

    p_traders = subparsers.add_parser("traders", help="Get market traders")
    p_traders.add_argument("market_id")
    p_traders.add_argument("--page", type=int, default=1)
    p_traders.add_argument("--limit", type=int, default=20)

    # ========== TRADE ==========
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

    p_positions = subparsers.add_parser("positions", help="Get positions")
    p_positions.add_argument("--page", type=int, default=1)
    p_positions.add_argument("--limit", type=int, default=20)

    p_history = subparsers.add_parser("trade-history", help="Get trade history")
    p_history.add_argument("--page", type=int, default=1)
    p_history.add_argument("--limit", type=int, default=20)

    # ========== USER ==========
    p_profile = subparsers.add_parser("profile", help="Get user profile")
    p_profile.add_argument("user_id", help="User ID (use 'me' for current user)")

    p_leader = subparsers.add_parser("leaderboard", help="Get leaderboard")
    p_leader.add_argument("--page", type=int, default=1)
    p_leader.add_argument("--limit", type=int, default=20)
    p_leader.add_argument("--timeframe", default="all")

    p_followers = subparsers.add_parser("followers", help="Get user followers")
    p_followers.add_argument("user_id")
    p_followers.add_argument("--page", type=int, default=1)
    p_followers.add_argument("--limit", type=int, default=20)

    p_following = subparsers.add_parser("following", help="Get users followed by user")
    p_following.add_argument("user_id")
    p_following.add_argument("--page", type=int, default=1)
    p_following.add_argument("--limit", type=int, default=20)

    p_favs = subparsers.add_parser("favorites", help="Get user favorites")
    p_favs.add_argument("user_id")
    p_favs.add_argument("--page", type=int, default=1)
    p_favs.add_argument("--limit", type=int, default=20)

    p_follow = subparsers.add_parser("follow", help="Follow a user")
    p_follow.add_argument("user_id")

    p_unfollow = subparsers.add_parser("unfollow", help="Unfollow a user")
    p_unfollow.add_argument("user_id")

    p_block = subparsers.add_parser("block", help="Block a user")
    p_block.add_argument("user_id")

    p_unblock = subparsers.add_parser("unblock", help="Unblock a user")
    p_unblock.add_argument("user_id")

    # ========== SOCIAL ==========
    p_comments = subparsers.add_parser("comments", help="Get market comments")
    p_comments.add_argument("market_id")
    p_comments.add_argument("--page", type=int, default=1)
    p_comments.add_argument("--limit", type=int, default=20)

    p_add_comment = subparsers.add_parser("add-comment", help="Add a comment")
    p_add_comment.add_argument("market_id")
    p_add_comment.add_argument("content")

    p_del_comment = subparsers.add_parser("delete-comment", help="Delete a comment")
    p_del_comment.add_argument("market_id")
    p_del_comment.add_argument("comment_id")

    p_fav = subparsers.add_parser("favorite", help="Favorite a market")
    p_fav.add_argument("market_id")

    p_unfav = subparsers.add_parser("unfavorite", help="Unfavorite a market")
    p_unfav.add_argument("market_id")

    # ========== CHALLENGES ==========
    subparsers.add_parser("challenges", help="List challenges")

    p_claim = subparsers.add_parser("claim-challenge", help="Claim challenge reward")
    p_claim.add_argument("challenge_id")

    # ========== ORACLE ==========
    p_oracle = subparsers.add_parser("oracle-status", help="Get oracle status")
    p_oracle.add_argument("prediction_id")

    p_assert = subparsers.add_parser("assert", help="Assert prediction result")
    p_assert.add_argument("prediction_id")
    p_assert.add_argument("option_id")

    p_dispute = subparsers.add_parser("dispute", help="Dispute prediction result")
    p_dispute.add_argument("prediction_id")
    p_dispute.add_argument("option_id")

    p_vote = subparsers.add_parser("vote", help="Vote on prediction result")
    p_vote.add_argument("prediction_id")
    p_vote.add_argument("option_id")

    p_settle = subparsers.add_parser("settle", help="Settle prediction")
    p_settle.add_argument("prediction_id")

    # ========== CATEGORIES ==========
    subparsers.add_parser("categories", help="List categories")

    # ========== CREATION ==========
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
    
    # Check for required environment variables
    missing = []
    if not os.getenv("SEESAW_BASE_URL"): missing.append("SEESAW_BASE_URL")
    if not os.getenv("SEESAW_API_KEY"): missing.append("SEESAW_API_KEY")
    if not os.getenv("SEESAW_API_SECRET"): missing.append("SEESAW_API_SECRET")
    
    if missing:
        print("\n" + "!" * 50)
        print("ERROR: SEESAW-AGENT IS UNINITIALIZED")
        print("!" * 50)
        print(f"Missing environment variables: {', '.join(missing)}")
        print("\nTo initialize, add these variables to your OpenClaw Gateway Config:")
        print("  - Use `gateway config.patch` to add them to 'env.vars'.")
        print("  - Or edit `openclaw.json` directly.")
        print("\nExample:")
        print("  gateway config.patch '{\"env\": {\"vars\": {\"SEESAW_BASE_URL\": \"https://app.seesaw.fun/v1\"}}}'")
        print("!" * 50 + "\n")
        sys.exit(1)

    client = SeesawClient()

    try:
        if args.command == "balance":
            print(json.dumps(client.get_balance(), indent=2))
        elif args.command == "transactions":
            print(json.dumps(client.get_transactions(args.page, args.limit), indent=2))
        elif args.command == "credit-history":
            print(json.dumps(client.get_credit_history(args.page, args.limit), indent=2))
        elif args.command == "daily-gift-status":
            print(json.dumps(client.get_daily_gift_status(), indent=2))
        elif args.command == "claim-daily-gift":
            print(json.dumps(client.claim_daily_gift(), indent=2))
        elif args.command == "list-markets":
            print(json.dumps(client.list_markets(args.page, args.limit, args.status, args.category_id), indent=2))
        elif args.command == "get-market":
            print(json.dumps(client.get_market(args.id), indent=2))
        elif args.command == "market-activity":
            print(json.dumps(client.get_market_activity(args.market_id, args.page, args.limit), indent=2))
        elif args.command == "price-history":
            print(json.dumps(client.get_price_history(args.market_id), indent=2))
        elif args.command == "holders":
            print(json.dumps(client.get_holders(args.market_id, args.page, args.limit), indent=2))
        elif args.command == "traders":
            print(json.dumps(client.get_traders(args.market_id, args.page, args.limit), indent=2))
        elif args.command == "quote":
            print(json.dumps(client.get_quote(args.market_id, args.option_id, args.amount, args.side), indent=2))
        elif args.command == "buy":
            print(json.dumps(client.buy(args.market_id, args.option_id, args.amount), indent=2))
        elif args.command == "sell":
            print(json.dumps(client.sell(args.market_id, args.option_id, args.shares), indent=2))
        elif args.command == "positions":
            print(json.dumps(client.get_positions(args.page, args.limit), indent=2))
        elif args.command == "trade-history":
            print(json.dumps(client.get_trade_history(args.page, args.limit), indent=2))
        elif args.command == "profile":
            print(json.dumps(client.get_profile(args.user_id), indent=2))
        elif args.command == "leaderboard":
            print(json.dumps(client.get_leaderboard(args.page, args.limit, args.timeframe), indent=2))
        elif args.command == "followers":
            print(json.dumps(client.get_followers(args.user_id, args.page, args.limit), indent=2))
        elif args.command == "following":
            print(json.dumps(client.get_following(args.user_id, args.page, args.limit), indent=2))
        elif args.command == "favorites":
            print(json.dumps(client.get_favorites(args.user_id, args.page, args.limit), indent=2))
        elif args.command == "follow":
            print(json.dumps(client.follow(args.user_id), indent=2))
        elif args.command == "unfollow":
            print(json.dumps(client.unfollow(args.user_id), indent=2))
        elif args.command == "block":
            print(json.dumps(client.block(args.user_id), indent=2))
        elif args.command == "unblock":
            print(json.dumps(client.unblock(args.user_id), indent=2))
        elif args.command == "comments":
            print(json.dumps(client.get_comments(args.market_id, args.page, args.limit), indent=2))
        elif args.command == "add-comment":
            print(json.dumps(client.add_comment(args.market_id, args.content), indent=2))
        elif args.command == "delete-comment":
            print(json.dumps(client.delete_comment(args.market_id, args.comment_id), indent=2))
        elif args.command == "favorite":
            print(json.dumps(client.favorite(args.market_id), indent=2))
        elif args.command == "unfavorite":
            print(json.dumps(client.unfavorite(args.market_id), indent=2))
        elif args.command == "challenges":
            print(json.dumps(client.list_challenges(), indent=2))
        elif args.command == "claim-challenge":
            print(json.dumps(client.claim_challenge(args.challenge_id), indent=2))
        elif args.command == "oracle-status":
            print(json.dumps(client.get_oracle_status(args.prediction_id), indent=2))
        elif args.command == "assert":
            print(json.dumps(client.assert_result(args.prediction_id, args.option_id), indent=2))
        elif args.command == "dispute":
            print(json.dumps(client.dispute_result(args.prediction_id, args.option_id), indent=2))
        elif args.command == "vote":
            print(json.dumps(client.vote(args.prediction_id, args.option_id), indent=2))
        elif args.command == "settle":
            print(json.dumps(client.settle(args.prediction_id), indent=2))
        elif args.command == "categories":
            print(json.dumps(client.list_categories(), indent=2))
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
