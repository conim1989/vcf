#!/usr/bin/env python3
"""
GitHub Commit Script for VCF Processor
This script provides a comprehensive way to commit and push changes to GitHub
with proper handling of relevant files and commit messages.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class GitHubCommit:
    def __init__(self):
        self.repo_root = Path(__file__).parent
        self.relevant_extensions = {
            '.py', '.js', '.html', '.css', '.json', '.yml', '.yaml',
            '.md', '.txt', '.cfg', '.ini', '.spec', '.svg'
        }
        self.ignore_patterns = {
            '__pycache__', '.DS_Store', '*.pyc', '*.pyo', '*.pyd',
            'build/', '*.egg-info/', '.pytest_cache/', '.venv/',
            'VCF_Processor_Release_*'
        }
    
    def run_command(self, command, check=True):
        """Run a shell command and return the result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {command}")
            print(f"Error: {e.stderr}")
            return None
    
    def get_git_status(self):
        """Get current git status."""
        return self.run_command("git status --porcelain")
    
    def get_staged_files(self):
        """Get list of staged files."""
        status = self.get_git_status()
        if not status:
            return []
        
        staged_files = []
        for line in status.split('\n'):
            if line and line[0] in ['A', 'M', 'R', 'C']:
                staged_files.append(line[3:])
        return staged_files
    
    def get_unstaged_files(self):
        """Get list of unstaged files."""
        status = self.get_git_status()
        if not status:
            return []
        
        unstaged_files = []
        for line in status.split('\n'):
            if line and line[1] in ['M', '?']:
                file_path = line[3:]
                if self.should_include_file(file_path):
                    unstaged_files.append(file_path)
        return unstaged_files
    
    def should_include_file(self, file_path):
        """Determine if a file should be included in the commit."""
        file_path = str(file_path)
        
        # Check ignore patterns
        ignore_patterns = {
            '__pycache__', '.DS_Store', '*.pyc', '*.pyo', '*.pyd',
            'build/', 'dist/', '*.egg-info/', '.pytest_cache/', '.venv/',
            'VCF_Processor_Release_*', 'VCF_Processor_Release_v*',
            'VCF_Processor_Fast/', 'VCF_Processor_Fixed/', 'VCF_Processor_Installer/'
        }
        
        # Check ignore patterns
        for pattern in ignore_patterns:
            if pattern in file_path or file_path.startswith(pattern):
                return False
        
        # Check file extension
        ext = Path(file_path).suffix.lower()
        if ext in self.relevant_extensions:
            return True
        
        # Check for files without extension (like requirements, Dockerfile)
        if not ext and Path(file_path).is_file():
            return True
        
        return False
    
    def stage_relevant_files(self):
        """Stage all relevant files for commit."""
        print("🔍 Scanning for relevant files to stage...")
        
        # Stage already tracked files
        tracked_files = self.run_command("git ls-files")
        if tracked_files:
            for file_path in tracked_files.split('\n'):
                if file_path and self.should_include_file(file_path):
                    if Path(file_path).exists():
                        self.run_command(f"git add '{file_path}'")
        
        # Stage new relevant files
        untracked_files = self.run_command("git ls-files --others --exclude-standard")
        if untracked_files:
            for file_path in untracked_files.split('\n'):
                if file_path and self.should_include_file(file_path):
                    self.run_command(f"git add '{file_path}'")
        
        print("✅ Relevant files staged successfully!")
    
    def generate_commit_message(self, custom_message=None):
        """Generate an appropriate commit message."""
        if custom_message:
            return custom_message
        
        # Get current branch
        branch = self.run_command("git rev-parse --abbrev-ref HEAD")
        
        # Get number of files changed
        staged = len(self.get_staged_files())
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Generate default message
        if staged > 0:
            return f"Update: {staged} files modified - {timestamp}"
        else:
            return f"Update: Code improvements - {timestamp}"
    
    def commit_changes(self, message=None):
        """Commit changes with the provided message."""
        if not message:
            message = self.generate_commit_message()
        
        print(f"📝 Committing with message: {message}")
        result = self.run_command(f'git commit -m "{message}"')
        if result is not None:
            print("✅ Changes committed successfully!")
            return True
        return False
    
    def push_changes(self, branch=None):
        """Push changes to remote repository."""
        if not branch:
            branch = self.run_command("git rev-parse --abbrev-ref HEAD")
        
        print(f"🚀 Pushing changes to {branch}...")
        result = self.run_command(f"git push origin {branch}")
        if result is not None:
            print("✅ Changes pushed to GitHub successfully!")
            return True
        return False
    
    def show_diff(self):
        """Show the diff of staged changes."""
        print("\n📊 Changes to be committed:")
        print("=" * 50)
        diff = self.run_command("git diff --cached --name-status")
        if diff:
            print(diff)
        else:
            print("No changes staged for commit.")
    
    def interactive_commit(self):
        """Interactive commit process."""
        print("\n" + "="*60)
        print("🎯 GitHub Commit Script for VCF Processor")
        print("="*60)
        
        # Show current status
        status = self.run_command("git status -s")
        if status:
            print("\n📋 Current Git Status:")
            print(status)
        
        # Show staged files
        staged = self.get_staged_files()
        if staged:
            print(f"\n📦 Already staged files ({len(staged)}):")
            for file in staged:
                print(f"  📄 {file}")
        
        # Show unstaged relevant files
        unstaged = self.get_unstaged_files()
        if unstaged:
            print(f"\n🔍 Unstaged relevant files ({len(unstaged)}):")
            for file in unstaged:
                print(f"  📄 {file}")
        
        print("\n" + "="*60)
        print("Options:")
        print("1. Stage all relevant files and commit")
        print("2. Use current staged files only")
        print("3. Custom commit message")
        print("4. Show diff")
        print("5. Cancel")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            self.stage_relevant_files()
            message = input("Enter commit message (leave empty for auto): ").strip()
            if self.commit_changes(message if message else None):
                if input("Push to GitHub? (y/n): ").lower() == 'y':
                    self.push_changes()
        
        elif choice == '2':
            if len(staged) == 0:
                print("❌ No files staged for commit.")
                return
            message = input("Enter commit message (leave empty for auto): ").strip()
            if self.commit_changes(message if message else None):
                if input("Push to GitHub? (y/n): ").lower() == 'y':
                    self.push_changes()
        
        elif choice == '3':
            message = input("Enter custom commit message: ").strip()
            if not message:
                print("❌ Commit message cannot be empty.")
                return
            self.stage_relevant_files()
            if self.commit_changes(message):
                if input("Push to GitHub? (y/n): ").lower() == 'y':
                    self.push_changes()
        
        elif choice == '4':
            self.show_diff()
        
        elif choice == '5':
            print("❌ Commit cancelled.")
        
        else:
            print("❌ Invalid choice.")

    def quick_commit(self, message=None):
        """Quick commit with default settings."""
        self.stage_relevant_files()
        if not message:
            message = self.generate_commit_message()
        
        if self.commit_changes(message):
            return self.push_changes()
        return False

if __name__ == "__main__":
    commit_tool = GitHubCommit()
    
    # Check if command line arguments provided
    if len(sys.argv) > 1:
        if sys.argv[1] == '--quick':
            message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None
            commit_tool.quick_commit(message)
        elif sys.argv[1] == '--diff':
            commit_tool.show_diff()
        else:
            commit_tool.commit_changes(' '.join(sys.argv[1:]))
            commit_tool.push_changes()
    else:
        commit_tool.interactive_commit()
