import os
import sys
import time
import shutil
import zipfile
import subprocess

def install_update():
    """Replace current exe with updated version"""
    try:
        # Wait for main app to close
        time.sleep(2)
        
        # Extract update
        with zipfile.ZipFile("update.zip", 'r') as zip_ref:
            zip_ref.extractall("update_temp")
        
        # Get current exe path
        current_exe = sys.argv[1] if len(sys.argv) > 1 else "VCF_Processor_Fast.exe"
        
        # Backup current version
        if os.path.exists(current_exe):
            shutil.move(current_exe, f"{current_exe}.backup")
        
        # Replace with new version
        new_exe = os.path.join("update_temp", os.path.basename(current_exe))
        if os.path.exists(new_exe):
            shutil.move(new_exe, current_exe)
        
        # Cleanup
        shutil.rmtree("update_temp", ignore_errors=True)
        os.remove("update.zip")
        
        # Restart app
        subprocess.Popen([current_exe])
        
    except Exception as e:
        print(f"Update failed: {e}")
        # Restore backup if update failed
        backup = f"{current_exe}.backup"
        if os.path.exists(backup):
            shutil.move(backup, current_exe)

if __name__ == "__main__":
    install_update()