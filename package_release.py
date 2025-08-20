#!/usr/bin/env python3
import os
import zipfile
import sys

def create_release_zip():
    dist_path = "dist/VCF_Processor_Fast"
    
    if not os.path.exists(dist_path):
        print("Error: dist/VCF_Processor_Fast folder not found. Build first.")
        return False
    
    # Get version from app.py
    try:
        with open("app.py", "r") as f:
            content = f.read()
            for line in content.split('\n'):
                if 'APP_VERSION = ' in line:
                    version = line.split('"')[1]
                    break
    except:
        version = "unknown"
    
    zip_name = f"VCF_Processor_Fast_v{version}.zip"
    
    print(f"Creating {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_path):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arc_name)
    
    print(f"Created {zip_name} ({os.path.getsize(zip_name) / 1024 / 1024:.1f} MB)")
    return zip_name

if __name__ == "__main__":
    zip_file = create_release_zip()
    if zip_file:
        print(f"Upload this file to GitHub release: {zip_file}")