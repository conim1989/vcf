"""
Integration of drag-and-drop functionality into app.py
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
        js_code = """
        document.body.classList.add('drag-over');
        const dropZone = document.querySelector('.drop-zone');
        if (dropZone) dropZone.classList.add('highlight');
        """
        self.window.evaluate_js(js_code)
        
    def on_drag_over(self, e):
        js_code = "event.preventDefault();"
        self.window.evaluate_js(js_code)
        
    def on_drag_leave(self, e):
        js_code = """
        document.body.classList.remove('drag-over');
        const dropZone = document.querySelector('.drop-zone');
        if (dropZone) dropZone.classList.remove('highlight');
        """
        self.window.evaluate_js(js_code)
        
    def on_drop(self, e):
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
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.vcf', '.vcf.gz')):
                            vcf_files.append(os.path.join(root, file))
        
        if vcf_files:
            self.update_ui_with_files(vcf_files)
            
    def update_ui_with_files(self, files):
        files_json = json.dumps(files)
        js_code = f"""
        const files = {files_json};
        const pathInput = document.getElementById('path-input');
        if (pathInput) {{
            pathInput.value = files.join('\\n');
        }}
        """
        self.window.evaluate_js(js_code)
        
    def bind_events(self):
        self.window.dom.document.events.dragenter += DOMEventHandler(self.on_drag_enter, True, True)
        self.window.dom.document.events.dragover += DOMEventHandler(self.on_drag_over, True, True)
        self.window.dom.document.events.dragleave += DOMEventHandler(self.on_drag_leave, True, True)
        self.window.dom.document.events.drop += DOMEventHandler(self.on_drop, True, True)

def bind_drag_drop(window, api_instance):
    handler = VCFDragDropHandler(window, api_instance)
    handler.bind_events()
    return handler
