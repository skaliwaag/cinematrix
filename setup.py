#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def copy_env():
    src = os.path.join(ROOT, "misc", ".env.example")
    for subdir in ("api", "bot"):
        dest = os.path.join(ROOT, subdir, ".env")
        if os.path.exists(dest):
            print(f"  {subdir}/.env already exists, skipping")
        else:
            shutil.copy(src, dest)
            print(f"  Created {subdir}/.env")


def install_deps():
    for subdir in ("api", "bot"):
        req = os.path.join(ROOT, subdir, "requirements.txt")
        print(f"  Installing {subdir} dependencies...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req, "-q"]
        )


def maybe_seed():
    answer = input("\nSeed the database with sample movies? [y/N] ").strip().lower()
    if answer == "y":
        script = os.path.join(ROOT, "api", "seed_db_updatecheck.py")
        subprocess.check_call(
            [sys.executable, script],
            cwd=os.path.join(ROOT, "api")
        )
        print("  Database seeded.")


if __name__ == "__main__":
    print("=== CineMatrix Setup ===\n")

    print("Step 1: Copying .env files...")
    copy_env()

    print("\nStep 2: Installing dependencies...")
    install_deps()

    maybe_seed()

    print("\nAll set! To run CineMatrix:")
    print("  Terminal 1 — start the API:  cd api && uvicorn main:app --reload")
    print("  Terminal 2 — start the bot:  cd bot && python bot.py")
