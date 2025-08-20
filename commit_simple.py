#!/usr/bin/env python3
"""
Simple GitHub commit script for VCF Processor
Handles Windows path issues correctly
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd):
    """Run command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def stage_files():
    """Stage relevant files using git commands."""
    print("🔍 Staging relevant files...")
    
    # Stage all tracked files that are modified
    run_command("git add -u")
    
    # Stage new files that should be tracked
    new_files = [
        "commit_to_github.py",
        "commit_simple.py",
        "commit.bat",
        "commit.sh",
        "clean_build_dirs.py",
        ".gitignore"
    ]
    
    for file in new_files:
        if os.path.exists(file):
            run_command(f"git add {file}")
    
    # Stage source files
    source_files = [
        "app.py",
        "vcf_extractor.py",
        "config.py",
        "updater.py",
        "package_release.py",
        "build_release.py",
        "installer.py",
        "update_installer.py"
    ]
    
    for file in source_files:
        if os.path.exists(file):
            run_command(f"git add {file}")
    
    # Stage web files
    web_files = [
        "static/styles.css",
        "static/wheel.svg",
        "templates/index_pt-br.html"
    ]
    
    for file in web_files:
        if os.path.exists(file):
            run_command(f"git add {file}")
    
    # Stage build specs
    build_specs = [
        "build.spec",
        "build_improved.spec",
        "build_installer.spec",
        "build_fixed.spec"
    ]
    
    for file in build_specs:
        if os.path.exists(file):
            run_command(f"git add {file}")
    
    print("✅ Files staged successfully!")

def commit_changes(message=None):
    """Commit changes with provided message."""
    if not message:
        message = f"Update: Code improvements - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print(f"📝 Committing: {message}")
    if run_command(f'git commit -m "{message}"'):
        print("✅ Changes committed!")
        return True
    return False

def push_changes():
    """Push changes to GitHub."""
    print("🚀 Pushing to GitHub...")
    if run_command("git push origin main"):
        print("✅ Changes pushed to GitHub!")
        return True
    return False

def show_status():
    """Show current git status."""
    print("\n📊 Current Git Status:")
    run_command("git status --short")

def main():
    print("=== VCF Processor GitHub Commit Tool ===")
    show_status()
    
    print("\nOptions:")
    print("1. Stage and commit all relevant files")
    print("2. Custom commit message")
    print("3. Show status")
    print("4. Cancel")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        stage_files()
        if commit_changes():
            if input("Push to GitHub? (y/n): ").lower() == 'y':
                push_changes()
    
    elif choice == '2':
        message = input("Enter commit message: ").strip()
        if message:
            stage_files()
            if commit_changes(message):
                if input("Push to GitHub? (y/n): ").lower() == 'y':
                    push_changes()
    
    elif choice == '3':
        show_status()
    
    elif choice == '4':
        print("❌ Cancelled")

if __name__ == "__main__":
    main()
