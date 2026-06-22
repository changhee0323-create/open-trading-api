"""
API client for the Samsung Auto Trader.
Provides a base HTTP client wrapper with error handling and retry logic.
"""

import logging
from typing import Dict, Any, Optional
import requests

from config import Config
from utils import safe_sleep


logger = logging.getLogger(__name__)


class APIClient:
    """
    Base HTTP client for KIS API requests.
    Handles errors, retries, and rate limiting.
    """
    
    def __init__(self, base_url: str, timeout: int = Config.REQUEST_TIMEOUT_SECONDS):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for API (e.g., https://openapi.ksmesrv.com)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
    
    def get(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> requests.Response:
        """
        Make a GET request with retry logic.
        
        Args:
            endpoint: API endpoint path
            headers: Request headers
            params: Query parameters
            retry_count: Current retry attempt (internal use)
        
        Returns:
            Response object
        
        Raises:
            requests.RequestException: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"GET {url}")
            response = requests.get(
                url,
                headers=headers or {},
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
        
        except requests.RequestException as e:
            if retry_count < Config.MAX_RETRIES:
                logger.warning(
                    f"GET {endpoint} failed (attempt {retry_count + 1}): {e}. "
                    f"Retrying in {Config.API_RETRY_DELAY_SECONDS}s..."
                )
                safe_sleep(Config.API_RETRY_DELAY_SECONDS)
                return self.get(endpoint, headers, params, retry_count + 1)
            else:
                logger.error(f"GET {endpoint} failed after {Config.MAX_RETRIES + 1} attempts: {e}")
                raise
    
    def post(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> requests.Response:
        """
        Make a POST request with retry logic.
        
        Args:
            endpoint: API endpoint path
            headers: Request headers
            json: JSON request body
            retry_count: Current retry attempt (internal use)
        
        Returns:
            Response object
        
        Raises:
            requests.RequestException: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"POST {url} with data: {json}")
            response = requests.post(
                url,
                headers=headers or {},
                json=json,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
        
        except requests.RequestException as e:
            if retry_count < Config.MAX_RETRIES:
                logger.warning(
                    f"POST {endpoint} failed (attempt {retry_count + 1}): {e}. "
                    f"Retrying in {Config.API_RETRY_DELAY_SECONDS}s..."
                )
                safe_sleep(Config.API_RETRY_DELAY_SECONDS)
                return self.post(endpoint, headers, json, retry_count + 1)
            else:
                logger.error(f"POST {endpoint} failed after {Config.MAX_RETRIES + 1} attempts: {e}")
                raise
    
    def check_api_error(self, response: requests.Response) -> Optional[Dict[str, Any]]:
        """
        Check if API response contains an error.
        
        Args:
            response: Response object
        
        Returns:
            Error data if present, None if success
        """
        try:
            data = response.json()
        except ValueError:
            # Not JSON response
            return None
        
        # Common KIS API error indicators
        if isinstance(data, dict):
            if data.get("rt_cd") != "0":  # rt_cd != "0" means error
                logger.error(f"API error response: {data}")
                return data
            
            if "error_description" in data:
                logger.error(f"API error: {data.get('error_description')}")
                return data
        
        return None


if __name__ == "__main__":
    from logger import setup_logger
    
    setup_logger(__name__, level="DEBUG")
    
    client = APIClient(Config.BASE_URL)
    print("✓ API client initialized")
