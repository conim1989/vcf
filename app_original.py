import os
import sys
import json
import webview
import threading
import importlib
from flask import Flask, render_template, request, jsonify
import time

from vcf_extractor import VCFProcessor
import subprocess
import configparser
import json
import ast
import os
import logging
from webview.dom import DOMEventHandler
import time
import signal # Import signal module


#  >>> Função para lidar com caminhos em modo de script e .exe
def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para dev e para PyInstaller """
    try:
        # PyInstaller cria uma pasta temp e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Setup ---
# <<< ALTERADO >>> Use a função resource_path para as pastas do Flask e arquivos de configuração
static_folder_path = resource_path('static')
template_folder_path = resource_path('templates')
app = Flask(__name__, static_folder=static_folder_path, template_folder=template_folder_path)

session_data = {}
session_lock = threading.Lock()

if getattr(sys, 'frozen', False):
    config_ini_path = os.path.join(sys._MEIPASS, 'config.ini')
else:
    config_ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

LOG_FILENAME = os.path.join(application_path, "NAO_APAGAR.log")
config_ini_path = os.path.join(application_path, 'config.ini')


# --- NEW: Global variable to hold startup data ---
# This is the reliable bridge between the main thread and the Flask thread.
initial_data_for_ui = {
    "vcf_path": "",
    "duplicates": []
}

def read_config_ini():
    # <<< ALTERADO >>> Adicionado tratamento de erro caso o config.ini não seja encontrado
    if not os.path.exists(config_ini_path):
        logging.error(f"ARQUIVO DE CONFIGURAÇÃO NÃO ENCONTRADO EM: {config_ini_path}")
        # Retorna valores padrão para que o programa não quebre
        return 'static', []
        
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

# --- Drag and Drop Functions (Copied from Signature Analyzer) ---

#lets set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def on_drag(e):
    pass

def on_drop(e):
    files = e['dataTransfer']['files']
    dropped_paths = []
    for file in files:
        path = file['pywebviewFullPath']
        # In VCF Processor, we only care about .vcf files or directories containing them
        if os.path.isfile(path) and path.lower().endswith(('.vcf',)):
            dropped_paths.append(path)
        elif os.path.isdir(path):
            # If a directory is dropped, we'll handle finding VCFs later if needed,
            # but for simplicity here, we'll just pass the directory path.
            dropped_paths.append(path)

    # Update the UI input field with the dropped path(s)
    # Assuming there's an input field with id 'vcf-path' in the VCF Processor UI
    # If multiple paths are dropped, we'll just show the first one or join them.
    # For simplicity here, let's just take the first valid path.
    if dropped_paths:
        js_code = f"""
        var path = {json.dumps(dropped_paths[0])};
        var inputElement = document.getElementById('vcf-path'); // Corrected ID
        if (inputElement) {{
            inputElement.value = path;
            // Dispatch a custom event to notify the frontend JS that the value has changed
            var event = new Event('droppedFileReady');
            inputElement.dispatchEvent(event);
        }} else {{
            console.error("Input element with id 'vcf-path' not found.");
        }}
        """
        window.evaluate_js(js_code)
    else:
         js_code = """
        var inputElement = document.getElementById('vcf-path'); // Corrected ID
        if (inputElement) {
            inputElement.value = ''; # Clear the input if no valid files were dropped
        }
        console.warn("No valid .vcf files or directories containing them were dropped.");
        """
         window.evaluate_js(js_code)


def bind(window):
    window.dom.document.events.dragenter += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragstart += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragover += DOMEventHandler(on_drag, True, True, debounce=500)
    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)
    # Add event listener for window closing
    window.events.closed += on_window_closed


# Function to handle window closing event
def on_window_closed():
    logger.info("Webview window closed. Shutting down Flask server.")
    # Trigger Flask server shutdown
    # This works by sending a request to a dedicated shutdown route
    try:
        import requests
        requests.post('http://12_0_0_1:5000/shutdown')
    except Exception as e:
        logger.error(f"Error sending shutdown request to Flask: {e}")
    finally:
        # Ensure the main Python process exits
        os._exit(0)


class Api:
    def __init__(self): self._window = None
    def set_window(self, window): self._window = window
    def select_file(self):
        # Modify select_file to filter for .vcf files
        file_paths = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False, # VCF Processor currently handles one file at a time
            file_types=('VCF Files (*.vcf)',)
        )
        # create_file_dialog returns a tuple or None. Return the first item if not None.
        return file_paths[0] if file_paths else None


    def close_window(self):
        """Destroys the window and triggers the closed event."""
        self._window.destroy()

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
        # <<< NOVO >>> Limpa o nome base de saída alternativo para evitar confusão
        session_data.pop('output_base_name', None)
    return jsonify({"duplicates": duplicate_contacts})

# <<< NOVO >>> Rota para processar o texto colado
@app.route('/start_text_processing', methods=['POST'])
def start_text_processing():
    data = request.get_json()
    text_content = data.get('text_content')
    if not text_content or not text_content.strip():
        return jsonify({"error": "Nenhum texto fornecido."}), 400

    log_path = LOG_FILENAME
    global LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE
    LIGHT_MODE_DEFAULT, TITLES_TO_REMOVE = read_config_ini()
    processor = VCFProcessor(log_file_path=log_path, titles_to_remove=TITLES_TO_REMOVE)
    
    # Usa o novo método do processador para extrair contatos do texto
    unique_contacts, duplicate_contacts = processor.get_unique_and_duplicate_contacts_from_text(text_content)
    
    with session_lock:
        session_data['processor'] = processor
        session_data['unique_contacts'] = unique_contacts
        # Define um nome de arquivo de saída padrão, já que não há arquivo de entrada
        session_data['output_base_name'] = "Contatos_Colados"
        # Limpa o caminho do vcf para evitar confusão
        session_data.pop('vcf_path', None)
        
    return jsonify({"duplicates": duplicate_contacts})


@app.route('/reprocess_selected', methods=['POST'])
def reprocess_selected():
    data = request.get_json()
    selected_to_reprocess = data.get('selected_to_reprocess', [])
    
    with session_lock:
        processor = session_data.get('processor')
        vcf_path = session_data.get('vcf_path')
        # <<< NOVO >>> Pega o nome base alternativo da sessão
        output_base_name = session_data.get('output_base_name')
        unique_contacts = session_data.get('unique_contacts', [])

    # <<< ALTERADO >>> Verifica se há um processador e *alguma* forma de nomear o arquivo de saída
    if not processor or (not vcf_path and not output_base_name):
        return jsonify({"error": "Sessão expirada. Por favor, comece de novo."}), 400

    numbers_to_remove = [contact['cleaned_number'] for contact in selected_to_reprocess]
    if numbers_to_remove:
        processor.remove_from_log(numbers_to_remove)
        
    contacts_to_process = unique_contacts + selected_to_reprocess
    
    # <<< ALTERADO >>> Determina o nome base para o arquivo de saída
    if vcf_path:
        base, _ = os.path.splitext(vcf_path)
    else:
        base = output_base_name

    # Passa o nome base determinado para a função de salvar
    output_file = processor.process_and_save(contacts_to_process, base)
    
    with session_lock:
        session_data.clear()
        
    return jsonify({"message": "Processamento concluído!", "output_file": output_file or "None"})


# Define the new Flask route for dropped files
@app.route('/process_dropped_vcf', methods=['POST'])
def process_dropped_vcf():
    data = request.get_json()
    vcf_path = data.get('vcf_path')

    if not vcf_path:
        return jsonify({"error": "VCF file path is missing from the request."}), 400

    # Validate the received path
    if not os.path.isfile(vcf_path) or not vcf_path.lower().endswith('.vcf'):
        return jsonify({"error": "Invalid or non-VCF file path provided."}), 400

    try:
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
            # <<< NOVO >>> Limpa o nome base de saída alternativo para evitar confusão
            session_data.pop('output_base_name', None)

        # Return the duplicates found, similar to the start_vcf_processing route
        return jsonify({"duplicates": duplicate_contacts}), 200

    except FileNotFoundError:
        return jsonify({"error": f"VCF file not found at: {vcf_path}"}), 404
    except Exception as e:
        logger.error(f"An error occurred during VCF processing: {e}", exc_info=True)
        return jsonify({"error": f"Failed to process VCF file: {e}"}), 500

# Add a shutdown route for Flask
@app.route('/shutdown', methods=['POST'])
def shutdown():
    # This function is a bit tricky to get right for shutting down a server
    # in a thread. The request.environ method is standard for Werkzeug.
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    shutdown_func()
    return 'Server shutting down...'




# --- Main Execution (with True Headless-First Logic) ---
if __name__ == '__main__':
    # Check if a valid file path is provided and it exists
    initial_file_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) and not sys.argv[1].startswith('-'):
         initial_file_path = sys.argv[1]


    if initial_file_path:
        print("--- Running in Headless Mode ---")
        log_path = LOG_FILENAME
        # NOTE: The VCFProcessor import failed previously. This code will still fail
        # unless vcf_extractor is available in the environment.
        try:
            processor = VCFProcessor(log_file_path=log_path, titles_to_remove=TITLES_TO_REMOVE)
            unique_contacts, duplicate_contacts = processor.get_unique_and_duplicate_contacts(initial_file_path)

            if not duplicate_contacts:
                print("No duplicates found. Processing unique contacts automatically.")
                # <<< ALTERADO >>> Passa o nome base para a função de salvar
                base, _ = os.path.splitext(initial_file_path)
                output_file = processor.process_and_save(unique_contacts, base)
                print(f"Headless processing complete. Output: {output_file or 'None'}")
                sys.exit(0)
            else:
                print(f"Found {len(duplicate_contacts)} duplicates. Preparing GUI...")
                initial_data_for_ui['vcf_path'] = initial_file_path
                initial_data_for_ui['duplicates'] = duplicate_contacts
                with session_lock:
                    session_data['processor'] = processor
                    session_data['vcf_path'] = initial_file_path
                    session_data['unique_contacts'] = unique_contacts
        except NameError:
             # Handle the case where VCFProcessor is not defined
            print("Error: VCFProcessor class not found. Please ensure vcf_extractor is available.")
            print("Proceeding to GUI mode without initial processing.")
            initial_data_for_ui['vcf_path'] = initial_file_path # Still pass the path to the GUI
            initial_data_for_ui['duplicates'] = [] # No duplicates to show
        except Exception as e:
             # Handle other potential exceptions during initial processing
            print(f"An error occurred during initial headless processing: {e}")
            print("Proceeding to GUI mode with error message.")
            initial_data_for_ui['vcf_path'] = initial_file_path
            initial_data_for_ui['duplicates'] = []
            # Optionally, add error handling to display this in the GUI log


    # This block now runs for both GUI-first and headless-with-duplicates cases
    print("Launching GUI mode...")
    api_instance = Api()
    # NOTE: The webview.create_window call requires the 'window' variable to be accessible
    # by the drag and drop functions (on_drop).
    # Pass the API instance to the window so JS can access it
    window = webview.create_window('VCF Processor', app, js_api=api_instance, width=800, height=750, frameless=True, resizable=True)
    api_instance.set_window(window)

    # Run Flask app in a separate thread
    # Make the Flask thread a daemon thread so it doesn't prevent the main process from exiting
    flask_thread = threading.Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False))
    flask_thread.daemon = True # Set as daemon thread
    flask_thread.start()
    time.sleep(1) # Give the Flask server a moment to start

    # Ensure the bind function is called to attach drag/drop events and window closing event
    webview.start(bind, window, debug=False, http_server=False) # http_server=False because Flask is running

    # Add a short sleep after webview.start to allow the shutdown request to be sent
    time.sleep(0.5)

    # Ensure the main thread exits after the webview window is closed
    sys.exit(0)