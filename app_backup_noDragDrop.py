# app.py (VCF Processor with Correct State Passing)

import os
import sys
import json
import webview
import threading
import importlib
from flask import Flask, render_template, request, jsonify

from vcf_extractor import VCFProcessor
import subprocess
import configparser
import json
import ast
import os

# --- Setup ---
app = Flask(__name__, static_folder='static')
session_data = {}
session_lock = threading.Lock()

LOG_FILENAME = os.path.join(os.path.abspath(os.path.dirname(__file__)), "NAO_APAGAR.log")

# --- NEW: Global variable to hold startup data ---
# This is the reliable bridge between the main thread and the Flask thread.
initial_data_for_ui = {
    "vcf_path": "",
    "duplicates": []
}

config_ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')

def read_config_ini():
    config = configparser.ConfigParser(allow_no_value=True)
    with open(config_ini_path, encoding='utf-8') as f:
        lines = f.readlines()
    # Remove lines that are part of the multi-line list to avoid parsing errors
    filtered_lines = []
    in_titles = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('titles_to_remove'):
            if stripped.endswith('['):
                in_titles = True
                filtered_lines.append('titles_to_remove = []\n')  # placeholder empty list
            else:
                filtered_lines.append(line)
        elif in_titles:
            if stripped == ']':
                in_titles = False
            # skip lines inside the list
        else:
            filtered_lines.append(line)
    config.read_string(''.join(filtered_lines))
    # Read light_mode from [Settings]
    light_mode = config.get('Settings', 'light_mode', fallback='static')
    # Read titles_to_remove manually
    titles_lines = []
    in_titles = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('titles_to_remove'):
            if stripped.endswith('['):
                in_titles = True
                continue
            else:
                titles_lines.append(stripped.split('=',1)[1].strip())
        elif in_titles:
            if stripped == ']':
                in_titles = False
            else:
                # Remove trailing commas and quotes, and strip spaces
                clean_line = stripped.rstrip(',').strip().strip('"').strip("'")
                if clean_line:
                    titles_lines.append(clean_line)
    # Construct JSON array string with proper commas and brackets
    titles_str = '[' + ','.join(f'"{line}"' for line in titles_lines) + ']'
    try:
        titles = json.loads(titles_str)
    except Exception:
        try:
            titles = ast.literal_eval(titles_str)
        except Exception:
            titles = []
    return light_mode, titles

LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE = read_config_ini()

class Api:
    def __init__(self): self._window = None
    def set_window(self, window): self._window = window
    def select_file(self): return self._window.create_file_dialog(webview.OPEN_DIALOG)
    def close_window(self): self._window.destroy()
    def minimize_window(self): self._window.minimize()
    def set_window_position(self, x, y): self._window.move(x, y)
    def open_log_file_with_notepad(self):
        """Opens the log file using the default notepad, since it is a .log file, it wont have an association with any application."""
        subprocess.run(["notepad.exe", LOG_FILENAME], check=True)       

    def open_file_path(self, path):
        """Safely opens a file path using the OS's default application."""
        if not os.path.exists(path):
            print(f"Error: Cannot open file, path does not exist: {path}")
            return
        
        print(f"Attempting to open file: {path}")
        try:
            if sys.platform == "win32":
                os.startfile(os.path.realpath(path))
            elif sys.platform == "darwin": # macOS
                subprocess.run(["open", path])
            else: # linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            print(f"Failed to open file: {e}")

api = Api()

# --- Flask Routes ---
@app.route('/')
def index():
    """
    Renders the UI, now correctly using the global variable for its initial state.
    """
    # --- THIS IS THE FIX ---
    # This function now reads the data that was prepared in the __main__ block.
    return render_template(
        'index_pt-br.html',
        window_title="Processador de VCF",
        initial_vcf_path=initial_data_for_ui["vcf_path"],
        initial_duplicates=json.dumps(initial_data_for_ui["duplicates"])
    )


config_file = 'config.ini'

def write_config(light_mode):
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
    if 'Settings' not in config:
        config['Settings'] = {}
    config['Settings']['light_mode'] = light_mode
    with open(config_file, 'w') as f:
        config.write(f)

def read_config():
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
        return config.get('Settings', 'light_mode', fallback='static')
    return 'static'

@app.route('/save_light_mode', methods=['POST'])
def save_light_mode():
    data = request.json
    # Save data['lightMode'] to user preferences or config
    light_mode = data.get('lightMode') or data.get('light_mode') or data.get('lightMode')
    if light_mode:
        # Manually read the config.ini file lines
        with open(config_ini_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Find the line with light_mode setting
        for i, line in enumerate(lines):
            if line.strip().startswith('light_mode'):
                lines[i] = f'light_mode = {light_mode}\n'
                break
        else:
            # If not found, add it under [Settings]
            for i, line in enumerate(lines):
                if line.strip() == '[Settings]':
                    lines.insert(i+1, f'light_mode = {light_mode}\n')
                    break
        # Write back to config.ini
        with open(config_ini_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    return jsonify({'status': 'success'})

@app.route('/get_light_mode', methods=['GET'])
def get_light_mode():
    # Load light mode preference
    light_mode = read_config_ini()[0]
    return jsonify({'lightMode': light_mode})


@app.route('/get_titles', methods=['GET'])
def get_titles():
    # Reload config.ini to get updated titles
    global LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE
    LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE = read_config_ini()
    titles = []
    titles = TITLES_TO_REMOVE
    titles.sort(key=str.lower)  # Sort titles case-insensitively
    return jsonify({"titles": titles})

@app.route('/save_titles', methods=['POST'])
def save_titles():
    new_titles = []
    data = request.get_json()
    new_titles = data.get('titles', [])
    new_titles.sort(key=str.lower)  # Sort titles case-insensitively
    try:
        # Manually read the config.ini file lines
        with open(config_ini_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Find the start and end of titles_to_remove list
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('titles_to_remove'):
                start_idx = i
                break
        if start_idx is not None:
            for j in range(start_idx + 1, len(lines)):
                if lines[j].strip() == ']':
                    end_idx = j
                    break
        # Prepare new titles lines with proper formatting
        new_titles_lines = ['titles_to_remove = [\n']
        for title in new_titles:
            new_titles_lines.append(f'    "{title}",\n')
        new_titles_lines.append(']\n')
        # Replace old titles lines with new ones
        if start_idx is not None and end_idx is not None:
            lines = lines[:start_idx] + new_titles_lines + lines[end_idx+1:]
        else:
            # Append if not found
            lines.extend(new_titles_lines)
        # Write back to config.ini
        with open(config_ini_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# route to get the processed numbers from the log file

@app.route('/get_processed_numbers', methods=['GET'])
def get_processed_numbers():
    """ Returns the list of processed numbers from the log file by sending them as an array.
    """
    try:
        with open(LOG_FILENAME, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        processed_numbers = [int(line.strip()) for line in lines if line.strip().isdigit()]
        return jsonify({"numbers": processed_numbers}), 200
    except FileNotFoundError:
        return jsonify({"error": "Log file not found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500    


# route to receive added numbers from the UI
@app.route('/add_processed_numbers', methods=['POST'])
def add_processed_numbers():
    """
    Receives a list of numbers to add to the processed numbers log.
    """
    data = request.get_json()
    if not data or 'numbers' not in data:
        return jsonify({"error": "No numbers provided."}), 400
    
    numbers_to_add = data['numbers']
    if not isinstance(numbers_to_add, list) or not all(isinstance(num, int) for num in numbers_to_add):
        return jsonify({"error": "Invalid input format. Expected a list of integers."}), 400
    
    try:
        with open(LOG_FILENAME, 'a', encoding='utf-8') as f:
            for number in numbers_to_add:
                f.write(f"{number}\n")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#route to receive removed numbers from the UI
@app.route('/remove_processed_numbers', methods=['POST'])
def remove_processed_numbers():
    """
    Receives a list of numbers to remove from the processed numbers log.
    """
    data = request.get_json()
    if not data or 'numbers' not in data:
        return jsonify({"error": "No numbers provided."}), 400
    
    numbers_to_remove = data['numbers']
    if not isinstance(numbers_to_remove, list) or not all(isinstance(num, int) for num in numbers_to_remove):
        return jsonify({"error": "Invalid input format. Expected a list of integers."}), 400
    
    try:
        with open(LOG_FILENAME, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(LOG_FILENAME, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip() not in map(str, numbers_to_remove):
                    f.write(line)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    """
    Returns the current session data, including the processor state and VCF path.
    """
    with session_lock:
        if not session_data:
            return jsonify({"error": "No session data available."}), 404
        return jsonify(session_data), 200 

@app.route('/start_vcf_processing', methods=['POST'])
def start_vcf_processing():
    data = request.get_json()
    vcf_path = data.get('vcf_path')
    if not vcf_path: return jsonify({"error": "VCF file path is required."}), 400
    log_path = LOG_FILENAME
    # Reload config.ini to get updated titles
    global LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE
    LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE = read_config_ini()
    processor = VCFProcessor(log_file_path=log_path, titles_to_remove=TITLES_TO_REMOVE)
    unique_contacts, duplicate_contacts = processor.get_unique_and_duplicate_contacts(vcf_path)
    with session_lock:
        session_data['processor'] = processor
        session_data['vcf_path'] = vcf_path
        session_data['unique_contacts'] = unique_contacts
    return jsonify({"duplicates": duplicate_contacts})

@app.route('/reprocess_selected', methods=['POST'])
def reprocess_selected():
    data = request.get_json()
    selected_to_reprocess = data.get('selected_to_reprocess', [])
    with session_lock:
        processor = session_data.get('processor')
        vcf_path = session_data.get('vcf_path')
        unique_contacts = session_data.get('unique_contacts', [])
    if not processor or not vcf_path:
        return jsonify({"error": "Session expired. Please start over."}), 400
    numbers_to_remove = [contact['cleaned_number'] for contact in selected_to_reprocess]
    if numbers_to_remove:
        processor.remove_from_log(numbers_to_remove)
    contacts_to_process = unique_contacts + selected_to_reprocess
    output_file = processor.process_and_save(vcf_path, contacts_to_process)
    with session_lock:
        session_data.clear()
    return jsonify({"message": "Processing complete!", "output_file": output_file or "None"})

# --- Main Execution (with True Headless-First Logic) ---
if __name__ == '__main__':
    initial_file_path = sys.argv[1] if len(sys.argv) > 1 else None


    if initial_file_path:
        print("--- Running in Headless Mode ---")
        if not os.path.exists(initial_file_path):
            print(f"Error: File not found at '{initial_file_path}'")
            sys.exit(1)
            
        log_path = LOG_FILENAME
        # Removed importlib.reload(config) since config is no longer imported
        processor = VCFProcessor(log_file_path=log_path, titles_to_remove=TITLES_TO_REMOVE)
        unique_contacts, duplicate_contacts = processor.get_unique_and_duplicate_contacts(initial_file_path)
        
        if not duplicate_contacts:
            print("No duplicates found. Processing unique contacts automatically.")
            output_file = processor.process_and_save(initial_file_path, unique_contacts)
            print(f"Headless processing complete. Output: {output_file or 'None'}")
            sys.exit(0)
        else:
            print(f"Found {len(duplicate_contacts)} duplicates. Preparing GUI...")
            # --- THIS IS THE FIX ---
            # Set the global data for the UI to use when it loads
            initial_data_for_ui['vcf_path'] = initial_file_path
            initial_data_for_ui['duplicates'] = duplicate_contacts
            with session_lock:
                session_data['processor'] = processor
                session_data['vcf_path'] = initial_file_path
                session_data['unique_contacts'] = unique_contacts

    # This block now runs for both GUI-first and headless-with-duplicates cases
    print("Launching GUI mode...")
    api_instance = Api()
    window = webview.create_window('VCF Processor', app, js_api=api_instance, width=800, height=750, frameless=True, resizable=True)
    api_instance.set_window(window)
    webview.start(debug=False, http_server=True)
