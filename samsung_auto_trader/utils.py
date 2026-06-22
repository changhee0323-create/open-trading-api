"""
Utility functions for the Samsung Auto Trader.
Includes time window checks, sleep helpers, and data manipulation.
"""

import time
from datetime import datetime
from typing import Tuple
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def get_current_time() -> datetime:
    """Get current datetime in Korean time (KST, UTC+9), regardless of system timezone."""
    return datetime.now(KST)


def is_within_trading_window(
    start_hour: int,
    start_minute: int,
    end_hour: int,
    end_minute: int
) -> bool:
    """
    Check if current time is within trading window.
    
    Args:
        start_hour: Trading window start hour (e.g., 9)
        start_minute: Trading window start minute (e.g., 10)
        end_hour: Trading window end hour (e.g., 15)
        end_minute: Trading window end minute (e.g., 30)
    
    Returns:
        True if current time is within window, False otherwise
    """
    now = get_current_time()
    current_time = (now.hour, now.minute)
    start_time = (start_hour, start_minute)
    end_time = (end_hour, end_minute)
    
    return start_time <= current_time <= end_time


def is_weekday() -> bool:
    """Check if today is a weekday (Monday=0 to Friday=4)."""
    today = get_current_time()
    return today.weekday() < 5  # 0-4 are Monday-Friday


def is_trading_day() -> bool:
    """
    Check if today is a valid trading day.
    Currently checks weekday only; can be extended for holidays.
    """
    return is_weekday()


def safe_sleep(seconds: float) -> None:
    """
    Sleep for given seconds, useful for rate limiting.
    
    Args:
        seconds: Number of seconds to sleep
    """
    if seconds > 0:
        time.sleep(seconds)


def time_until_trading_start(
    start_hour: int,
    start_minute: int
) -> Tuple[int, int, int]:
    """
    Calculate time remaining until trading window starts.
    
    Args:
        start_hour: Trading window start hour
        start_minute: Trading window start minute
    
    Returns:
        Tuple of (hours, minutes, seconds) remaining
    """
    now = get_current_time()
    start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    
    # If start time has passed today, return 0
    if now >= start:
        return (0, 0, 0)
    
    delta = start - now
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return (hours, minutes, seconds)


def format_price(price: int) -> str:
    """Format price as KRW with comma separator."""
    return f"{price:,} KRW"


def format_time_remaining(hours: int, minutes: int, seconds: int) -> str:
    """Format time remaining as HH:MM:SS."""
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


if __name__ == "__main__":
    print(f"Current time: {get_current_time()}")
    print(f"Is weekday: {is_weekday()}")
    print(f"Is trading day: {is_trading_day()}")
    print(f"Within trading window (09:10-15:30): {is_within_trading_window(9, 10, 15, 30)}")
