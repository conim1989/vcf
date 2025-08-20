#!/usr/bin/env python3
import os
import subprocess
import shutil
import zipfile

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print("Success!")
    return True

def build_release():
    print("Building VCF Processor Release")
    print("=" * 40)
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Build main app
    print("\n1. Building main application...")
    if not run_command("pyinstaller build_improved.spec"):
        return False
    
    # Build installer
    print("\n2. Building installer...")
    if not run_command("pyinstaller build_installer.spec"):
        return False
    
    # Move installer to dist folder
    print("\n3. Organizing files...")
    installer_src = "dist/VCF_Processor_Installer.exe"
    installer_dst = "dist/VCF_Processor_Installer.exe"
    
    if os.path.exists(installer_src):
        print("Installer ready in dist folder")
    else:
        print("Error: Installer not found")
        return False
    
    # Create release zip
    print("\n4. Creating release package...")
    
    # Get version
    version = "unknown"
    try:
        with open("app.py", "r") as f:
            for line in f:
                if 'APP_VERSION = ' in line:
                    version = line.split('"')[1]
                    break
    except:
        pass
    
    zip_name = f"VCF_Processor_Release_v{version}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add main app folder
        for root, dirs, files in os.walk("dist/VCF_Processor_Fast"):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, "dist")
                zipf.write(file_path, arc_name)
        
        # Add installer
        zipf.write("dist/VCF_Processor_Installer.exe", "VCF_Processor_Installer.exe")
    
    print(f"\n✓ Release package created: {zip_name}")
    print(f"  Size: {os.path.getsize(zip_name) / 1024 / 1024:.1f} MB")
    
    # Publish to GitHub
    print("\n5. Publishing to GitHub...")
    release_notes = f"VCF Processor v{version} - Complete installer package with auto-install, shortcuts, and file associations."
    
    if not run_command(f'gh release create v{version} --title "VCF Processor v{version}" --notes "{release_notes}"'):
        print("Warning: Failed to create GitHub release")
    else:
        if not run_command(f'gh release upload v{version} "{zip_name}"'):
            print("Warning: Failed to upload release file")
        else:
            print(f"\n✓ Published to GitHub: https://github.com/conim1989/vcf/releases/tag/v{version}")
    
    print(f"\nUsers can:")
    print(f"1. Download {zip_name} from GitHub")
    print(f"2. Extract and run VCF_Processor_Installer.exe for auto-install")
    print(f"3. Or run VCF_Processor_Fast/VCF_Processor_Fast.exe directly")
    
    return True

if __name__ == "__main__":
    if build_release():
        input("\nPress Enter to exit...")
    else:
        input("\nBuild failed. Press Enter to exit...")