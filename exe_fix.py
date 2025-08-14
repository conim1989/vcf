#!/usr/bin/env python3
"""
Critical fix for PyInstaller exe VCF processing
Add this code to the beginning of your main app.py file
"""

import os
import sys

# CRITICAL FIX: Set working directory to exe location
if getattr(sys, 'frozen', False):
    # Running as PyInstaller exe
    exe_dir = os.path.dirname(sys.executable)
    os.chdir(exe_dir)
    print(f"EXE MODE: Changed working directory to: {exe_dir}")
    
    # Ensure all file operations use absolute paths relative to exe
    def get_exe_relative_path(filename):
        return os.path.join(exe_dir, filename)
else:
    # Running as script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"SCRIPT MODE: Working directory: {script_dir}")
    
    def get_exe_relative_path(filename):
        return os.path.join(script_dir, filename)

# Export the function for use in other modules
__all__ = ['get_exe_relative_path']