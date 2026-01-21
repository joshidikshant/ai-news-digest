"""
LinkedIn Carousel Generator — Gamma API

Generates PDF carousels from curated AI news items using Gamma.app.

Usage:
  python generate_carousel.py                    # Process recent (48h)
  python generate_carousel.py --date 2026-01-21  # Specific date
  
Requires:
  GAMMA_API_KEY environment variable (Gamma Pro subscription $15/mo)
"""

import os
import json
import glob
import argparse
import asyncio
from datetime import datetime, timedelta, timezone as python_timezone
from typing import List, Dict


class Config:
    GAMMA_API_KEY = os.getenv("GAMMA_API_KEY")
    DATA_DIR = "data"
    SLIDING_WINDOW_HOURS = 48


def get_recent_curated_files(hours: int = 48) -> List[str]:
    """Get curated files from the last N hours."""
    curated_dir = os.path.join(Config.DATA_DIR, "curated")
    curated_files = glob.glob(os.path.join(curated_dir, "*.json"))
    
    if not curated_files:
        return []
    
    now = datetime.now(python_timezone.utc)
    cutoff = now - timedelta(hours=hours)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")
    
    return [f for f in sorted(curated_files) if os.path.splitext(os.path.basename(f))[0] >= cutoff_date_str]


async def main():
    parser = argparse.ArgumentParser(
        description="Generate LinkedIn carousels using Gamma API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate carousels for recent data (48h)
  python generate_carousel.py
  
  # Generate for a specific date
  python generate_carousel.py --date 2026-01-21
  
  # Set image quality
  python generate_carousel.py --image-quality premium

Environment:
  GAMMA_API_KEY - Your Gamma.app API key (Pro plan required)
"""
    )
    
    parser.add_argument("--date", help="Date to process (YYYY-MM-DD)")
    parser.add_argument("--all", action="store_true", help="Process all curated files")
    parser.add_argument("--theme", choices=["dark", "light"], default="dark", help="Color theme")
    parser.add_argument(
        "--image-quality",
        choices=["none", "basic", "advanced", "premium"],
        default=os.getenv("GAMMA_IMAGE_QUALITY", "basic"),
        help="AI image quality tier (default: basic)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not Config.GAMMA_API_KEY:
        print("❌ GAMMA_API_KEY not set!")
        print()
        print("To use this generator:")
        print("  1. Get a Gamma Pro subscription ($15/mo) at gamma.app")
        print("  2. Get your API key from gamma.app/settings/api")
        print("  3. Set the environment variable:")
        print("     export GAMMA_API_KEY='your_api_key'")
        return
    
    # Import provider
    from providers import get_provider
    
    provider = get_provider(
        "gamma",
        theme=args.theme,
        image_quality=args.image_quality
    )
    
    print(f"🎠 Gamma Carousel Generator")
    print(f"   Theme: {args.theme}")
    print(f"   Image Quality: {args.image_quality}")
    print()
    
    if args.date:
        await provider.process_day(args.date)
    elif args.all:
        curated_files = glob.glob(os.path.join(Config.DATA_DIR, "curated", "*.json"))
        curated_files.sort()
        print(f"Processing ALL {len(curated_files)} curated days...")
        for f in curated_files:
            date_str = os.path.splitext(os.path.basename(f))[0]
            print(f"\n=== {date_str} ===")
            await provider.process_day(date_str)
    else:
        recent_files = get_recent_curated_files(Config.SLIDING_WINDOW_HOURS)
        
        if not recent_files:
            print(f"No curated data in the last {Config.SLIDING_WINDOW_HOURS} hours.")
            return
        
        # Limit to the SINGLE most recent day to strictly enforce 1 carousel/run
        latest_file = recent_files[-1:]
        print(f"Processing {len(latest_file)} day (latest only)...")
        for f in latest_file:
            date_str = os.path.splitext(os.path.basename(f))[0]
            print(f"\n=== {date_str} ===")
            await provider.process_day(date_str)


if __name__ == "__main__":
    asyncio.run(main())
