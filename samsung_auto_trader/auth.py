"""
Authentication module for the Samsung Auto Trader.
Handles token acquisition, caching, and refresh logic.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from config import Config


logger = logging.getLogger(__name__)


class TokenCache:
    """Manages token caching in a JSON file."""
    
    def __init__(self, cache_file: Path):
        """
        Initialize token cache.
        
        Args:
            cache_file: Path to token cache JSON file
        """
        self.cache_file = cache_file
    
    def save_token(self, token: str, app_key: str, token_type: str = "Bearer") -> None:
        """
        Save token, app_key and timestamp to cache.

        Args:
            token: Access token string
            app_key: App key the token was issued for (used to invalidate cache on key rotation)
            token_type: Token type (default: Bearer)
        """
        cache_data = {
            "token": token,
            "app_key": app_key,
            "token_type": token_type,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().date().isoformat()
        }

        with open(self.cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Token cached to {self.cache_file}")

    def load_token(self, app_key: str) -> Optional[Dict[str, Any]]:
        """
        Load token from cache if it exists, is from today, and matches the current app_key.

        Args:
            app_key: Current app_key; cache is discarded if it was issued for a different key

        Returns:
            Dictionary with token data, or None if cache invalid/expired
        """
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read cache file: {e}")
            return None

        # Check if token is from today
        cached_date = cache_data.get("date")
        today = datetime.now().date().isoformat()

        if cached_date != today:
            logger.info("Cached token is from a different day; will refresh")
            return None

        if cache_data.get("app_key") != app_key:
            logger.info("Cached token was issued for a different app_key; will refresh")
            return None

        logger.info("Using cached token from today")
        return cache_data
    
    def clear_cache(self) -> None:
        """Clear the token cache file."""
        if self.cache_file.exists():
            self.cache_file.unlink()
            logger.info("Token cache cleared")


class KISAuthenticator:
    """Handles authentication with KIS Open API."""
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str,
        token_endpoint: str,
        cache_file: Path
    ):
        """
        Initialize authenticator.
        
        Args:
            app_key: KIS application key
            app_secret: KIS application secret
            base_url: KIS API base URL
            token_endpoint: Token endpoint path
            cache_file: Path to token cache file
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self.token_endpoint = token_endpoint
        self.cache = TokenCache(cache_file)
        self._token: Optional[str] = None
    
    def get_token(self) -> str:
        """
        Get a valid access token, using cache if available.
        
        Returns:
            Access token string
        
        Raises:
            Exception: If token acquisition fails
        """
        # Try to use cached token first
        cached = self.cache.load_token(self.app_key)
        if cached:
            self._token = cached["token"]
            return self._token
        
        # Fetch new token
        logger.info("Fetching new authentication token from KIS...")
        return self._fetch_new_token()
    
    def _fetch_new_token(self) -> str:
        """
        Fetch a new token from KIS API.
        
        Returns:
            Access token string
        
        Raises:
            Exception: If token request fails
        """
        url = f"{self.base_url}{self.token_endpoint}"
        
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=Config.REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Token request failed: {e}")
            raise
        
        data = response.json()
        
        # Extract token from response
        # Note: Field name may vary; adjust if needed based on KIS API response
        token = data.get("access_token")
        
        if not token:
            logger.error(f"No access token in response: {data}")
            raise ValueError("Token not found in API response")
        
        # Cache the token
        self.cache.save_token(token, self.app_key)
        self._token = token
        logger.info("New token acquired and cached")
        
        return token
    
    def get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """
        Get standard headers for API requests.
        
        Args:
            include_auth: Whether to include Authorization header
        
        Returns:
            Dictionary of headers
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if include_auth:
            token = self._token or self.get_token()
            headers["Authorization"] = f"Bearer {token}"
        
        return headers


# ── 모듈 레벨 인터페이스 (trader.py 호환) ─────────────────────────────────────
import config as _cfg

_shared_auth: Optional[KISAuthenticator] = None


def _shared() -> KISAuthenticator:
    global _shared_auth
    if _shared_auth is None:
        _shared_auth = KISAuthenticator(
            app_key=_cfg.APP_KEY,
            app_secret=_cfg.APP_SECRET,
            base_url=_cfg.BASE_URL,
            token_endpoint=_cfg.TOKEN_ENDPOINT,
            cache_file=_cfg.TOKEN_CACHE_FILE,
        )
    return _shared_auth


def _convert_tr_id(tr_id: str) -> str:
    """모의투자 모드일 때 TR_ID 첫 글자 T/J/C → V 로 변환."""
    if _cfg.ENV_DV == "demo" and tr_id and tr_id[0] in ("T", "J", "C"):
        return "V" + tr_id[1:]
    return tr_id


def get_token() -> str:
    return _shared().get_token()


def make_headers(tr_id: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "authorization": f"Bearer {get_token()}",
        "appkey": _cfg.APP_KEY,
        "appsecret": _cfg.APP_SECRET,
        "tr_id": _convert_tr_id(tr_id),
    }


if __name__ == "__main__":
    from logger import setup_logger
    setup_logger(__name__, level="DEBUG")
    try:
        token = get_token()
        print(f"✓ Token acquired: {token[:20]}...")
    except Exception as e:
        print(f"✗ Auth error: {e}")
