#!/bin/bash

# Create GitHub release using GitHub CLI
# Run: chmod +x create_release.sh && ./create_release.sh

gh release create v2.0.0 \
  --title "VCF Processor v2.0.0" \
  --notes "## 🚀 VCF Processor v2.0.0

### ✨ New Features
- **Auto-updater system** - Get notified of new versions automatically
- **Global drag & drop** - Drop VCF files anywhere in the app
- **Live search** - Search through duplicates and filtered titles
- **Smooth animations** - Success/error visual feedback
- **Enhanced UI** - Better button layouts and interactions

### 🔧 Improvements  
- Virtual scrolling for large contact lists (1000+ items)
- Optimized CPU usage with stability algorithms
- AppData config storage for user settings
- Multiple title input support (paste lists)
- Improved error handling

### 📥 Installation
Download the exe file below and run it. No installation required!" \
  dist/VCF_Processor_Fast/VCF_Processor_Fast.exe