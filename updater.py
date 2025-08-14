import requests
import json
import os
import sys
import subprocess
from packaging import version

GITHUB_REPO = "conim1989/vcf"
CURRENT_VERSION = "2.0.0"  # Update this with each release

def check_for_updates():
    try:
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"].lstrip("v")
            
            if version.parse(latest_version) > version.parse(CURRENT_VERSION):
                return {
                    "update_available": True,
                    "version": latest_version,
                    "download_url": latest_release["assets"][0]["browser_download_url"],
                    "changelog": latest_release["body"]
                }
    except Exception as e:
        print(f"Update check failed: {e}")
    
    return {"update_available": False}

def download_and_install_update(download_url):
    try:
        # Download update
        response = requests.get(download_url)
        update_file = "update.zip"
        
        with open(update_file, "wb") as f:
            f.write(response.content)
        
        # Extract and replace (simplified)
        import zipfile
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall("update_temp")
        
        # Launch updater script and exit
        subprocess.Popen([sys.executable, "update_installer.py"])
        sys.exit(0)
        
    except Exception as e:
        print(f"Update failed: {e}")
        return False