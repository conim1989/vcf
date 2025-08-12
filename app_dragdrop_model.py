from flask import Flask, render_template, request, jsonify
import threading
import tempfile
import shutil
import webview
import os
from multiprocessing import cpu_count
import json
import subprocess
import logging
import csv # <--- IMPORT THE CSV MODULE
from webview.dom import DOMEventHandler
import time

def on_drag(e):
    pass

def on_drop(e):
    files = e['dataTransfer']['files']
    dropped_paths = []
    for file in files:
        path = file['pywebviewFullPath']
        if os.path.isfile(path):
            if path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic', '.heif', '.pdf')):
                dropped_paths.append(path)
        elif os.path.isdir(path):
            dropped_paths.append(path)
    js_code = """ 
    document.getElementById('path-input').value = `{}`;
    selectedFiles = {};
    """.format(json.dumps('\n'.join(dropped_paths)), json.dumps(dropped_paths))
    window.evaluate_js(js_code)

def bind(window):
    window.dom.document.events.dragenter += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragstart += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragover += DOMEventHandler(on_drag, True, True, debounce=500)
    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)

#lets set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Set up Flask app

def expose(window):
    pass


app = Flask(__name__)
window = None
analysis_results = {}
analysis_lock = threading.Lock()

class API:
    def __init__(self, window):
        self._window = window


    
    def closeWindow(self):
        if self._window:
            self._window.destroy()
        os._exit(0)

    def minimizeWindow(self):
        if self._window:
            self._window.minimize()

    def set_window_position(self, x, y):
        if self._window:
            self._window.move(x, y)

    def select_folder(self):
        file_paths = self._window.create_file_dialog(webview.FOLDER_DIALOG, allow_multiple=True)
        
        return file_paths
    
    def select_file(self):
        file_paths = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=('Image Files (*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff;*.heic;*.heiff;*.pdf)',)
        )
        return file_paths




@app.route('/')
def index():
    return render_template('index_pt.html')

@app.route('/start_analysis', methods=['POST'])
def start_analysis_route():
    logger.info("start_analysis_route function called")
    data = request.get_json()
    paths = data.get('path')
    analysis_id = str(len(analysis_results))
    logger.info(f"Analysis ID: {analysis_id}")

    if not paths:
        return jsonify({"error": "Path is missing"}), 400
    temp_dir = "C:\\sign\\"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_dir_to_clean = None
    try:
        temp_dir_to_clean = tempfile.mkdtemp(prefix="sig_analyzer_session_", dir=temp_dir)
        logger.debug(f"Created temporary directory: {temp_dir_to_clean}")

        all_files_copied = False
        for path in paths:
            if os.path.isfile(path):
                shutil.copy(path, temp_dir_to_clean)
                all_files_copied = True
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heif', '.heic', '.pdf')):
                            shutil.copy(os.path.join(root, file), temp_dir_to_clean)
                            all_files_copied = True
        
        if not all_files_copied:
             return jsonify({"error": "No valid files found in the selected paths"}), 400

        path_to_process = temp_dir_to_clean

        # --- NEW: Count total files for the progress bar ---
        import glob
        files_to_process = glob.glob(os.path.join(path_to_process, '*.*'))
        total_files = len(files_to_process)

        args = {
            'verbose': True,
            'ocr_width': int(data.get('ocrWidth', 1500)),
            'analysis_width': int(data.get('analysisWidth', 1000)),
            'target_phrase': data.get('targetPhrase', "assinatura do titular da conta"),
            'use_python_fallback': True,
            'debug_folder': "debug_output",
            'enable_image_debug': data.get('enableDebug', False),
            'workers': max(1, cpu_count() - 1)
        }

        analysis_results[analysis_id] = {
            'log': [],
            'results': [],
            'status': 'running',
            'total_files': total_files, # Store the total count for the frontend
        }
        
        thread = threading.Thread(
            target=run_analysis_wrapper, 
            args=(analysis_id, path_to_process, args, temp_dir_to_clean)
        )
        thread.start()
        
        logger.info(f"Analysis {analysis_id} started for path: {path_to_process}")
        return jsonify({"analysis_id": analysis_id}), 202

    except Exception as e:
        logger.error(f"An error occurred during analysis setup: {e}", exc_info=True)
        if temp_dir_to_clean:
            shutil.rmtree(temp_dir_to_clean)
        return jsonify({"error": f"Failed to start analysis: {e}"}), 500
# --- MODIFICATION: REVISED THE ENTIRE WRAPPER FUNCTION ---
def run_analysis_wrapper(analysis_id, path, args_dict, temp_dir_to_clean):
    command = [
        "python", "signature_analyzer.py", path,
        "--ocr-width", str(args_dict["ocr_width"]),
        "--analysis-width", str(args_dict["analysis_width"]),
        "--target-phrase", args_dict["target_phrase"],
        "--workers", str(args_dict["workers"]),
    ]
    if args_dict.get("verbose"): command.append("--verbose")
    if args_dict.get("use_python_fallback"): command.append("--use-python-fallback")
    if args_dict.get("enable_image_debug"): command.append("--enable-image-debug")
    if args_dict.get("debug_folder"): command.extend(["--debug-folder", args_dict["debug_folder"]])

    try:
        logger.info(f"Running command: {' '.join(command)}")

        os.environ['PYTHONIOENCODING'] = 'utf-8'
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding='utf-8',
            errors='replace'
        )

        # --- KEY CHANGE: Process stdout line-by-line ---
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue

            try:
                # Attempt to parse each line as a JSON object
                result = json.loads(line)
                with analysis_lock:
                    # Map the detailed result to the structure the frontend expects
                    analysis_results[analysis_id]['results'].append({
                        "file": result.get("source", "N/A"),
                        "status": result.get("status", "Error"),
                        "phrase_found": str(result.get("phrase_found", False)),
                        "signature_found": str(result.get("signature_found", False))
                    })
            except json.JSONDecodeError:
                # If it's not JSON, treat it as a standard log message
                with analysis_lock:
                    analysis_results[analysis_id]["log"].append(line)
        
        process.wait()
        return_code = process.returncode

        # The CSV parsing logic is now completely removed.

        with analysis_lock:
            analysis_results[analysis_id]["status"] = "complete" if return_code == 0 else "error"
            if return_code != 0:
                 analysis_results[analysis_id]["log"].append(f"Analysis script failed with return code {return_code}")

    except Exception as e:
        logger.error(f"An unhandled error occurred in the analysis thread: {e}", exc_info=True)
        with analysis_lock:
            analysis_results[analysis_id]["status"] = "error"
            analysis_results[analysis_id]["log"].append(str(e))
    finally:
        try:
            shutil.rmtree(temp_dir_to_clean)
        except PermissionError:
            import time
            time.sleep(1)  # wait for 1 second
            try:
                shutil.rmtree(temp_dir_to_clean)
            except Exception as e:
                logger.warning(f"Failed to delete temporary directory: {e}. This directory will be cleaned up eventually.")

@app.route('/analysis_status', methods=['POST'])
def analysis_status():
    analysis_id = request.get_json().get('analysis_id')
    with analysis_lock:
        data = analysis_results.get(analysis_id)
        if not data:
            return jsonify({"error": "Analysis ID not found"}), 404
        
        # Return the progress metrics along with the results
        return jsonify({
            'log': data['log'],
            'results': data['results'],
            'status': data['status'],
            'total_files': data.get('total_files', 0)
        })

if __name__ == '__main__':
    window = webview.create_window('Signature Analyzer', 'http://localhost:5000', width=800, height=950, frameless=True, easy_drag=False, resizable=True, min_size=(600, 500))
    api = API(window)
    window.expose(api.closeWindow, api.minimizeWindow, api.set_window_position, api.select_folder, api.select_file)
    threading.Thread(target=lambda: app.run(port=5000)).start()
    webview.start(bind, window, gui='edge', debug=False)