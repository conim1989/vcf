#!/usr/bin/env python3
"""
Script to remove build directories from git tracking
"""

import subprocess
import os

def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def clean_build_directories():
    """Remove build directories from git tracking."""
    print("🧹 Cleaning build directories from git tracking...")
    
    # Files and directories to remove from tracking
    to_remove = [
        "build/",
        "VCF_Processor_Release_v2.3.0/",
        "VCF_Processor_Release_v2.5.0/",
        "VCF_Processor_Release_v2.6.0/",
        "VCF_Processor_Fast_dummy.exe"
    ]
    
    removed_count = 0
    for item in to_remove:
        stdout, stderr, returncode = run_command(f"git rm -r --cached {item}")
        if returncode == 0:
            print(f"✅ Removed {item} from git tracking")
            removed_count += 1
        else:
            print(f"⚠️  {item} not found in git tracking or already removed")
    
    if removed_count > 0:
        print(f"\n🎯 Removed {removed_count} build directories from git tracking")
        print("📋 You can now commit these changes to update .gitignore")
    else:
        print("\n✨ No build directories found in git tracking")

if __name__ == "__main__":
    clean_build_directories()
