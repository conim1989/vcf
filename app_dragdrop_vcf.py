"""
Drag-and-drop handler for VCF files, adapted from app_dragdrop_model.py
"""

import os
import json
import webview
from webview.dom import DOMEventHandler
import threading
import time

class VCFDragDropHandler:
    def __init__(self, window, api_instance):
        self.window = window
        self.api = api_instance
        self.dropped_files = []
        
    def on_drag_enter(self, e):
        """Handle drag enter event"""
        js_code = """
        document.body.classList.add('drag-over');
        document.querySelector('.drop-zone').classList.add('highlight');
        """
        self.window.evaluate_js(js_code)
        
    def on_drag_over(self, e):
        """Handle drag over event - prevent default to allow drop"""
        js_code = """
        event.preventDefault();
        """
        self.window.evaluate_js(js_code)
        
    def on_drag_leave(self, e):
        """Handle drag leave event"""
        js_code = """
        document.body.classList.remove('drag-over');
        document.querySelector('.drop-zone').classList.remove('highlight');
        """
        self.window.evaluate_js(js_code)
        
    def on_drop(self, e):
        """Handle drop event for VCF files"""
        js_code = """
        event.preventDefault();
        document.body.classList.remove('drag-over');
        document.querySelector('.drop-zone').classList.remove('highlight');
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
            self.dropped_files = vcf_files
            self.update_ui_with_files(vcf_files)
            self.process_dropped_files(vcf_files)
            
    def update_ui_with_files(self, files):
        """Update UI with dropped VCF files"""
        files_json = json.dumps(files)
        js_code = f"""
        // Update file list display
        const fileList = document.getElementById('dropped-files');
        if (fileList) {{
            fileList.innerHTML = '';
            const files = {files_json};
            files.forEach(file => {{
                const item = document.createElement('div');
                item.className = 'file-item';
                item.textContent = file.split('/').pop();
                fileList.appendChild(item);
            }});
        }}
        
        // Update path input if exists
        const pathInput = document.getElementById('path-input');
        if (pathInput) {{
            pathInput.value = files.join('\\n');
        }}
        """
I have reviewed the contents of app.py. It is a Flask-based VCF processor with a webview UI, but it currently lacks drag-and-drop support.

Plan to adapt drag-and-drop from app_dragdrop_model.py to app.py:

Information Gathered:
- app_dragdrop_model.py has drag-and-drop handlers for images/PDFs using webview DOM events.
- app.py is a Flask app with VCF processing logic and webview UI but no drag-and-drop.
- app.py uses webview.create_window with js_api for API communication.
- app_dragdrop_model.py uses window.dom.document.events to bind drag-and-drop events.
- app_dragdrop_model.py filters files by image/pdf extensions; we need to filter for .vcf files.
- app_dragdrop_model.py updates UI input fields via JavaScript injection; app.py uses Flask templates and webview.

Plan:
- Add drag-and-drop event binding in app.py's webview window setup, similar to app_dragdrop_model.py's bind function.
- Implement drag event handlers (dragenter, dragover, drop) in app.py, adapted to accept only .vcf files and folders.
- Modify JavaScript injection in drop handler to update the UI with selected VCF file paths.
- Update Flask templates (e.g., index_pt-br.html) to include drag-and-drop zones and input fields compatible with the new handlers.
- Ensure the drag-and-drop handlers integrate with the existing start_vcf_processing route to process dropped files.
- Maintain thread safety and session data handling as in app.py.

Dependent Files to be edited:
- app.py (add drag-and-drop handlers and binding)
- templates/index_pt-br.html (add drag-and-drop UI elements and JavaScript)

Followup steps:
- Implement the above changes.
- Test drag-and-drop functionality with VCF files.
- Verify UI updates and processing flow.

Please confirm if I should proceed with this plan or if you want me to adjust or add anything.
