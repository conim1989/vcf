"""
Drag-and-drop handler for VCF files, adapted from app_dragdrop_model.py
"""

import os
import json
import webview
from webview.dom import DOMEventHandler

class VCFDragDropHandler:
    def __init__(self, window, api_instance):
        self.window = window
        self.api = api_instance
        
    def on_drag_enter(self, e):
        """Handle drag enter event"""
        js_code = """
        document.body.classList.add('drag-over');
        const dropZone = document.querySelector('.drop-zone');
        if (dropZone) dropZone.classList.add('highlight');
        """
        self.window.evaluate_js(js_code)
        
    def on_drag_over(self, e):
        """Handle drag over event"""
        js_code = """
        event.preventDefault();
        """
        self.window.evaluate_js(js_code)
        
    def on_drag_leave(self, e):
        """Handle drag leave event"""
        js_code = """
        document.body.classList.remove('drag-over');
        const dropZone = document.querySelector('.drop-zone');
        if (dropZone) dropZone.classList.remove('highlight');
        """
        self.window.evaluate_js(js_code)
        
    def on_drop(self, e):
        """Handle drop event for VCF files"""
        js_code = """
        event.preventDefault();
        document.body.classList.remove('drag-over');
        const dropZone = document.querySelector('.drop-zone');
        if (dropZone) dropZone.classList.remove('highlight');
        """
        self.window.evaluate_js(js_code)
        
        files = e['dataTransfer']['files']
        vcf_files = []
        
        for file in files:
            path = file['pywebviewFullPath']
            if os.path.isfile(path):
                if path.lower().endswith(('.vcf', '.vcf.gz')):
                    vcf_files.append(path)
            elif os.path.isdir(path):
                # Scan directory for VCF files
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.vcf', '.vcf.gz')):
                            vcf_files.append(os.path.join(root, file))
        
        if vcf_files:
            self.update_ui_with_files(vcf_files)
            
    def update_ui_with_files(self, files):
        """Update UI with dropped VCF files"""
        files_json = json.dumps(files)
        js_code = f"""
        const files = {files_json};
        if (files.length === 1) {{
            // Single file - update path input
            const pathInput = document.getElementById('path-input');
            if (pathInput) {{
                pathInput.value = files[0];
            }}
            // Trigger processing
            if (window.processVCF) {{
                window.processVCF(files[0]);
            }}
        }} else {{
            // Multiple files - show list and trigger processing
            const fileList = document.getElementById('dropped-files');
            if (fileList) {{
                fileList.innerHTML = '';
                files.forEach(file => {{
                    const item = document.createElement('div');
                    item.className = 'file-item';
                    item.textContent = file.split(/[\\\\/]/).pop();
                    fileList.appendChild(item);
                }});
            }}
            if (window.processMultipleVCFs) {{
                window.processMultipleVCFs(files);
            }}
        }}
        """
        self.window.evaluate_js(js_code)
        
    def bind_events(self):
        """Bind drag-and-drop events to the window"""
        self.window.dom.document.events.dragenter += DOMEventHandler(self.on_drag_enter, True, True)
        self.window.dom.document.events.dragover += DOMEventHandler(self.on_drag_over, True, True)
        self.window.dom.document.events.dragleave += DOMEventHandler(self.on_drag_leave, True, True)
        self.window.dom.document.events.drop += DOMEventHandler(self.on_drop, True, True)

def bind_drag_drop(window, api_instance):
    """Bind drag-and-drop functionality to the window"""
    handler = VCFDragDropHandler(window, api_instance)
    handler.bind_events()
    return handler
