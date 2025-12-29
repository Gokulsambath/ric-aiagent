import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.configs.migration import migrate

if __name__ == "__main__":
    print("Running migrations...")
    try:
        migrate()
        print("Migrations complete!")
    except Exception as e:
        print(f"Migration failed: {e}")
