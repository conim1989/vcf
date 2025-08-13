#!/usr/bin/env python3
"""
Build script for creating a fixed VCF Processor executable
This script will build the exe with proper VCF processing support
"""

import os
import sys
import subprocess
import shutil

def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'pyinstaller',
        'pandas',
        'openpyxl',
        'unidecode',
        'flask',
        'pywebview'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed")
    return True

def build_exe():
    """Build the executable using PyInstaller"""
    spec_file = "build_improved.spec"
    
    if not os.path.exists(spec_file):
        print(f"❌ Spec file {spec_file} not found")
        return False
    
    print(f"Building executable using {spec_file}...")
    
    try:
        # Run PyInstaller
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            spec_file
        ], check=True, capture_output=True, text=True)
        
        print("✅ Build completed successfully!")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def test_exe():
    """Test if the built executable works"""
    exe_path = os.path.join("dist", "VCF_Processor_Fixed", "VCF_Processor_Fixed.exe")
    
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found at {exe_path}")
        return False
    
    print(f"✅ Executable found at {exe_path}")
    print(f"File size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
    
    # You can add more tests here if needed
    return True

def main():
    """Main build process"""
    print("🔧 VCF Processor - Fixed Build Script")
    print("=" * 40)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        return 1
    
    # Step 2: Clean previous builds
    clean_build_dirs()
    
    # Step 3: Build executable
    if not build_exe():
        return 1
    
    # Step 4: Test executable
    if not test_exe():
        return 1
    
    print("\n🎉 Build process completed successfully!")
    print("The fixed executable is in: dist/VCF_Processor_Fixed/")
    print("\nTo test VCF processing:")
    print("1. Copy a .vcf file to the same directory as the .exe")
    print("2. Run the .exe and try processing the VCF file")
    print("3. Check the debug logs: vcf_debug.log and app_debug.log")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())