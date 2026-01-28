#!/usr/bin/env python3
"""
Setup script for 小红书 (XHS) login.

This script opens a browser window for you to scan the QR code and log in.
After successful login, the browser state is saved for future automated use.

Usage:
    python scripts/setup_xhs_login.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.xhs_service import XHSService


async def main():
    """Run the XHS login setup."""
    print("=" * 50)
    print("小红书 (XHS) Login Setup")
    print("=" * 50)
    print()

    # Create service with headless=False so we can see the QR code
    xhs = XHSService(headless=False)

    # Check if already logged in
    print("Checking if already logged in...")
    if await xhs.is_logged_in():
        print("✓ Already logged in to 小红书!")
        await xhs.close()
        return

    print("Not logged in. Opening browser for QR code login...")
    print()
    print("INSTRUCTIONS:")
    print("1. A browser window will open with the XHS login page")
    print("2. Open the 小红书 app on your phone")
    print("3. Scan the QR code to log in")
    print("4. Wait for the login to complete")
    print()

    success = await xhs.login_with_qr(timeout=120)

    if success:
        print()
        print("✓ Login successful!")
        print("✓ Browser state saved for future use")
        print()
        print("You can now close this window and run the main application.")
    else:
        print()
        print("✗ Login failed or timed out")
        print("Please try again.")

    await xhs.close()


if __name__ == "__main__":
    asyncio.run(main())
