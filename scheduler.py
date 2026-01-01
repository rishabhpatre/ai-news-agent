#!/usr/bin/env python3
"""
Scheduler for AI News Agent.

Runs the digest at a configured time daily using the schedule library.
For production, consider using system cron or a task scheduler.

Usage:
    python scheduler.py           # Run scheduler (blocking)
    python scheduler.py --once    # Run once immediately
"""

import argparse
import time
import sys
from datetime import datetime
from pathlib import Path

import schedule

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from agent import AINewsAgent


def run_daily_digest():
    """Run the daily digest job."""
    print(f"\n⏰ Scheduled run triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        agent = AINewsAgent()
        agent.run(dry_run=False, days_back=1)
    except Exception as e:
        print(f"❌ Scheduled run failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI News Agent Scheduler',
    )
    parser.add_argument(
        '--once', '-o',
        action='store_true',
        help='Run once immediately instead of scheduling',
    )
    parser.add_argument(
        '--time', '-t',
        type=str,
        default=None,
        help='Override send time (HH:MM format, 24-hour)',
    )
    
    args = parser.parse_args()
    
    if args.once:
        # Run immediately
        run_daily_digest()
        return
    
    # Get send time
    send_time = args.time or settings.send_time
    
    # Validate time format
    try:
        datetime.strptime(send_time, '%H:%M')
    except ValueError:
        print(f"❌ Invalid time format: {send_time}. Use HH:MM (24-hour)")
        sys.exit(1)
    
    # Schedule daily job
    schedule.every().day.at(send_time).do(run_daily_digest)
    
    print(f"🤖 AI News Agent Scheduler")
    print(f"{'='*40}")
    print(f"📧 Recipient: {settings.recipient_email or 'Not configured'}")
    print(f"⏰ Scheduled time: {send_time}")
    print(f"{'='*40}")
    print(f"\nScheduler running... Press Ctrl+C to stop.\n")
    
    # Show next run time
    next_run = schedule.next_run()
    if next_run:
        print(f"Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n👋 Scheduler stopped.")
        sys.exit(0)


if __name__ == '__main__':
    main()
