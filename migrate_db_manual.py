#!/usr/bin/env python3
"""
Manual migration utility for RIC AI Agent.
This script can be run to manually check and apply database migrations.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.migration_utils import run_migrations, check_pending_migrations, generate_migration_if_needed

def main():
    """Main function to run manual migration process."""
    print("=== RIC AI Agent - Manual Migration Utility ===")
    print()
    
    # Check if there are pending migrations
    print("Checking for pending migrations...")
    if check_pending_migrations():
        print("⚠️  Pending model changes detected!")
        response = input("Do you want to generate a new migration? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            if generate_migration_if_needed():
                print("✅ New migration generated successfully.")
            else:
                print("❌ Failed to generate migration.")
                return 1
        else:
            print("Skipping migration generation.")
    else:
        print("✅ No pending migrations found.")
    
    # Run migrations
    print("\nApplying all pending migrations...")
    try:
        run_migrations()
        print("✅ Migration process completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())