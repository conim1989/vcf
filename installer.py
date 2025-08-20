#!/usr/bin/env python3
import os
import sys
import shutil
import winreg
import ctypes
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def install_vcf_processor():
    # Get current directory (where installer is running from)
    if getattr(sys, 'frozen', False):
        source_dir = os.path.dirname(sys.executable)
    else:
        source_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try Program Files first, fallback to other locations
    install_locations = [
        "C:\\Program Files\\VCF Processor",
        "C:\\VCF Processor", 
        os.path.expanduser("~/Documents/VCF Processor")
    ]
    
    install_dir = None
    for location in install_locations:
        try:
            os.makedirs(location, exist_ok=True)
            # Test write access
            test_file = os.path.join(location, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            install_dir = location
            break
        except:
            continue
    
    if not install_dir:
        print("Error: Could not find writable installation directory")
        return False
    
    print(f"Installing to: {install_dir}")
    
    # Copy files
    try:
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        shutil.copytree(source_dir, install_dir)
    except Exception as e:
        print(f"Error copying files: {e}")
        return False
    
    exe_path = os.path.join(install_dir, "VCF_Processor_Fast.exe")
    
    # Create shortcuts
    create_shortcuts(exe_path)
    
    # Create file association
    create_file_association(exe_path)
    
    print("Installation completed successfully!")
    return True

def create_shortcuts(exe_path):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        
        # Desktop shortcut
        desktop = shell.SpecialFolders("Desktop")
        shortcut = shell.CreateShortCut(os.path.join(desktop, "VCF Processor.lnk"))
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        
        # Start Menu shortcut
        start_menu = shell.SpecialFolders("StartMenu")
        programs = os.path.join(start_menu, "Programs")
        shortcut = shell.CreateShortCut(os.path.join(programs, "VCF Processor.lnk"))
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        
        print("Shortcuts created")
    except Exception as e:
        print(f"Could not create shortcuts: {e}")

def create_file_association(exe_path):
    try:
        # Register .vcf file association
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\\Classes\\.vcf") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "VCFProcessor.File")
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\\Classes\\VCFProcessor.File") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "VCF Contact File")
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\\Classes\\VCFProcessor.File\\shell\\open\\command") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe_path}" "%1"')
        
        print("File association created")
    except Exception as e:
        print(f"Could not create file association: {e}")

if __name__ == "__main__":
    print("VCF Processor Installer")
    print("======================")
    
    if install_vcf_processor():
        input("Press Enter to exit...")
    else:
        input("Installation failed. Press Enter to exit...")