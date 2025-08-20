import requests
import json
import os
import sys
import subprocess
from packaging import version

GITHUB_REPO = "conim1989/vcf"

def get_current_version():
    try:
        from app import APP_VERSION
        return APP_VERSION
    except ImportError:
        return "2.0.0"  # Fallback

def check_for_updates():
    try:
        current_version = get_current_version()
        print(f"DEBUG: Current version: {current_version}")
        
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        print(f"DEBUG: API response status: {response.status_code}")
        
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"].lstrip("v")
            print(f"DEBUG: Latest version: {latest_version}")
            print(f"DEBUG: Assets count: {len(latest_release['assets'])}")
            
            version_comparison = version.parse(latest_version) > version.parse(current_version)
            print(f"DEBUG: Version comparison ({latest_version} > {current_version}): {version_comparison}")
            
            if version_comparison:
                if latest_release["assets"]:
                    print(f"DEBUG: Update available, returning data")
                    return {
                        "update_available": True,
                        "version": latest_version,
                        "download_url": latest_release["assets"][0]["browser_download_url"],
                        "changelog": latest_release["body"]
                    }
                else:
                    print(f"DEBUG: No assets found")
            else:
                print(f"DEBUG: No update needed")
        else:
            print(f"DEBUG: API request failed with status {response.status_code}")
    except Exception as e:
        print(f"Update check failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"DEBUG: Returning no update available")
    return {"update_available": False}

def download_and_install_update(download_url):
    try:
        # Get current exe directory
        if getattr(sys, 'frozen', False):
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        print(f"DEBUG: Current directory: {current_dir}")
        
        # Download update
        response = requests.get(download_url)
        update_file = os.path.join(current_dir, "update.zip")
        
        with open(update_file, "wb") as f:
            f.write(response.content)
        
        print(f"DEBUG: Downloaded to: {update_file}")
        
        # Extract to current directory
        import zipfile
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall(current_dir)
        
        print(f"DEBUG: Extracted to: {current_dir}")
        
        # Clean up
        os.remove(update_file)
        
        print("Update installed successfully. Please restart the application.")
        return True
        
    except Exception as e:
        print(f"Update failed: {e}")
        import traceback
        traceback.print_exc()
        return False