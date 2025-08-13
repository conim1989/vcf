# vcf_extractor.py

import io
import os
import sys # <<< ADICIONADO >>> Necessário para a correção do caminho de saída
import re
import pandas as pd
from unidecode import unidecode
import configparser
import json
import ast
import logging # <<< ADICIONADO >>> Para diagnóstico

# Configure logging for PyInstaller builds
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    log_dir = os.path.dirname(sys.executable)
else:
    # Running in normal Python environment
    log_dir = os.path.dirname(os.path.abspath(__file__))

log_file = os.path.join(log_dir, 'vcf_debug.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def read_titles_from_config_ini():
    if getattr(sys, 'frozen', False):
        config_ini_path = os.path.join(sys._MEIPASS, 'config.ini')
    else:
        config_ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    try:
        with open(config_ini_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        titles = []
        in_titles = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('titles_to_remove'):
                in_titles = True
                continue
            elif in_titles:
                if stripped == ']':
                    break
                elif stripped and not stripped.startswith('#'):
                    # Remove quotes and commas
                    title = stripped.strip('"').strip("'").rstrip(',')
                    if title:
                        titles.append(title)
        
        return titles
    except Exception as e:
        print(f"Error reading config.ini: {e}")
        return []

class VCFProcessor:
    def __init__(self, log_file_path, titles_to_remove=None):
        import os
        if not os.path.isabs(log_file_path):
            log_file_path = os.path.abspath(log_file_path)
        self.log_file_path = log_file_path
        if titles_to_remove is None:
            try:
                titles_to_remove = read_titles_from_config_ini()
            except Exception as e:
                print(f"Warning: Could not read titles from config: {e}")
                titles_to_remove = []
        if titles_to_remove:
            self.title_pattern = r'\b(' + '|'.join(re.escape(title) for title in titles_to_remove) + r')\.?\b'
            self.title_regex = re.compile(self.title_pattern, re.IGNORECASE)
        else:
            self.title_regex = None
        self.processed_numbers_log = self._read_log()

    def _read_vcf(self, vcf_file_path):
        # Enhanced VCF reading with better error handling for PyInstaller builds
        try:
            # Ensure absolute path
            if not os.path.isabs(vcf_file_path):
                vcf_file_path = os.path.abspath(vcf_file_path)
            
            # Check if file exists
            if not os.path.exists(vcf_file_path):
                print(f"VCF file not found: {vcf_file_path}")
                logging.error(f"VCF file not found: {vcf_file_path}")
                return None
            
            # Check file size
            file_size = os.path.getsize(vcf_file_path)
            print(f"Reading VCF file: {vcf_file_path} (Size: {file_size} bytes)")
            logging.info(f"Reading VCF file: {vcf_file_path} (Size: {file_size} bytes)")
            
            # Try multiple encodings
            encodings = ['utf-8', 'utf-8-sig', 'iso-8859-1', 'cp1252', 'latin1']
            
            for encoding in encodings:
                try:
                    with open(vcf_file_path, 'r', encoding=encoding, errors='replace') as f:
                        content = f.read()
                    
                    # Validate VCF content
                    if 'BEGIN:VCARD' in content and 'END:VCARD' in content:
                        print(f"VCF file read successfully with {encoding} encoding. Content length: {len(content)}")
                        logging.info(f"VCF file read successfully with {encoding} encoding. Content length: {len(content)}")
                        return content
                    else:
                        print(f"Invalid VCF content with {encoding} encoding")
                        continue
                        
                except UnicodeDecodeError as e:
                    print(f"Failed to read with {encoding}: {e}")
                    continue
                except Exception as e:
                    print(f"Error reading with {encoding}: {e}")
                    continue
            
            # If all encodings fail, try binary mode as last resort
            try:
                with open(vcf_file_path, 'rb') as f:
                    raw_content = f.read()
                # Try to decode as utf-8 with error handling
                content = raw_content.decode('utf-8', errors='replace')
                if 'BEGIN:VCARD' in content and 'END:VCARD' in content:
                    print("VCF file read in binary mode with UTF-8 fallback")
                    logging.info("VCF file read in binary mode with UTF-8 fallback")
                    return content
            except Exception as e:
                print(f"Binary mode reading failed: {e}")
                logging.error(f"Binary mode reading failed: {e}")
            
            print("Failed to read VCF file with any encoding")
            logging.error("Failed to read VCF file with any encoding")
            return None
            
        except Exception as e:
            print(f"Critical error reading VCF file: {e}")
            logging.error(f"Critical error reading VCF file: {e}", exc_info=True)
            return None

    def _extract_contact_data(self, vcf_content):
        """Extract contact data from VCF content with enhanced error handling"""
        contacts = []
        
        try:
            # Normalize line endings
            vcf_content = vcf_content.replace('\r\n', '\n').replace('\r', '\n')
            
            # Split into VCF blocks
            vcard_blocks = vcf_content.split("BEGIN:VCARD")
            
            print(f"Processing {len(vcard_blocks) - 1} VCF blocks")
            logging.info(f"Processing {len(vcard_blocks) - 1} VCF blocks")
            
            for i, block in enumerate(vcard_blocks):
                if "END:VCARD" not in block:
                    continue
                    
                name, waid = None, None
                
                try:
                    # Extract name - try multiple patterns
                    fn_patterns = [
                        r'FN:(.+?)(?:\n|\r|$)',
                        r'N:([^;\n\r]+)',
                        r'NICKNAME:(.+?)(?:\n|\r|$)'
                    ]
                    
                    for pattern in fn_patterns:
                        fn_match = re.search(pattern, block, re.MULTILINE)
                        if fn_match:
                            name = fn_match.group(1).strip()
                            break
                    
                    # Extract phone number - try multiple patterns
                    tel_patterns = [
                        r'TEL[^:]*:([+]?\d[\d\s\-\(\)]+)',
                        r'waid=([^:;\s]+)',
                        r'PHONE[^:]*:([+]?\d[\d\s\-\(\)]+)',
                        r'X-WA-BIZ-NAME[^:]*:.*?([+]?\d{10,15})'
                    ]
                    
                    for pattern in tel_patterns:
                        matches = re.findall(pattern, block, re.MULTILINE | re.IGNORECASE)
                        if matches:
                            # Clean the phone number
                            for match in matches:
                                cleaned = re.sub(r'[^\d+]', '', match)
                                if len(cleaned) >= 10:  # Valid phone number length
                                    waid = cleaned
                                    break
                            if waid:
                                break
                    
                    if name and waid:
                        contacts.append({'name': name, 'number': waid})
                        try:
                            print(f"Extracted contact: {name} -> {waid}")
                        except UnicodeEncodeError:
                            print(f"Extracted contact: [Unicode name] -> {waid}")
                    elif name:
                        try:
                            print(f"Contact found but no valid phone: {name}")
                        except UnicodeEncodeError:
                            print("Contact found but no valid phone: [Unicode name]")
                    elif waid:
                        print(f"Phone found but no name: {waid}")
                        
                except Exception as e:
                    print(f"Error processing VCF block {i}: {e}")
                    logging.error(f"Error processing VCF block {i}: {e}")
                    continue
            
            print(f"Successfully extracted {len(contacts)} contacts from VCF")
            logging.info(f"Successfully extracted {len(contacts)} contacts from VCF")
            return contacts
            
        except Exception as e:
            print(f"Critical error in VCF extraction: {e}")
            logging.error(f"Critical error in VCF extraction: {e}", exc_info=True)
            return []

    def _extract_contacts_from_text(self, text_content):
        contacts = []
        print(f"Starting contact data extraction from raw text.")
        padrao_1 = re.compile(r"✅\s*(.*?)\s*(\+\d+)\s*foi adicionado com sucesso\s*✅")
        matches_1 = padrao_1.findall(text_content)
        for nome, numero in matches_1:
            nome_limpo = nome.replace('*', '').strip()
            contacts.append({'name': nome_limpo, 'number': numero})
        padrao_2 = re.compile(r"Name:\s*(.*?)\s*Number \(1\):\s*(.*)")
        matches_2 = padrao_2.findall(text_content)
        for nome, numero_bruto in matches_2:
            numero_limpo = '+' + ''.join(filter(str.isdigit, numero_bruto))
            contacts.append({'name': nome.strip(), 'number': numero_limpo})
        print(f"Finished text extraction. Found {len(contacts)} potential contacts.")
        return contacts

    def _clean_name(self, name):
        if not name: return ""
        ascii_name = unidecode(name)
        cleaned_name = re.sub(r'[^a-zA-Z0-9\s]+', '', ascii_name)
        if self.title_regex: cleaned_name = self.title_regex.sub('', cleaned_name)
        cleaned_name = ' '.join(cleaned_name.split())
        words = cleaned_name.split()
        return words[0].title() if words else ""

    def _clean_phone_number(self, number):
        return re.sub(r'\D', '', number) if number else ""

    def _read_log(self):
        processed_numbers = set()
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    processed_numbers.update(line.strip() for line in f)
                print(f"Loaded {len(processed_numbers)} processed numbers from log.")
            except Exception as e:
                print(f"Error reading log file '{self.log_file_path}': {e}")
        return processed_numbers

    def remove_from_log(self, numbers_to_remove):
        if not os.path.exists(self.log_file_path) or not numbers_to_remove: return
        with open(self.log_file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip() not in numbers_to_remove: f.write(line)
        print(f"Removed {len(numbers_to_remove)} numbers from the log.")
        self.processed_numbers_log = self._read_log()

    def _sort_contacts_by_log(self, extracted_contacts):
        unique_contacts, duplicate_contacts = [], []
        for contact in extracted_contacts:
            cleaned_number = self._clean_phone_number(contact.get('number'))
            if cleaned_number:
                contact_data = {
                    'original_name': contact.get('name'),
                    'original_number': contact.get('number'),
                    'cleaned_number': cleaned_number
                }
                if cleaned_number in self.processed_numbers_log:
                    duplicate_contacts.append(contact_data)
                else:
                    unique_contacts.append(contact_data)
        return unique_contacts, duplicate_contacts

    def get_unique_and_duplicate_contacts(self, vcf_file_path):
        """Process VCF file with enhanced error handling for PyInstaller builds"""
        vcf_content = self._read_vcf(vcf_file_path)
        if vcf_content is None:
            return [], []
        
        extracted_contacts = self._extract_contact_data(vcf_content)
        return self._sort_contacts_by_log(extracted_contacts)

    def get_unique_and_duplicate_contacts_from_text(self, text_content):
        if not text_content or not text_content.strip():
            return [], []
        extracted_contacts = self._extract_contacts_from_text(text_content)
        return self._sort_contacts_by_log(extracted_contacts)

    def process_and_save(self, contacts_to_process, output_base_name):
        if not contacts_to_process: return None
        output_data, newly_processed_numbers = [], set()
        for contact in contacts_to_process:
            cleaned_number = contact['cleaned_number']
            cleaned_name = self._clean_name(contact['original_name'])
            if cleaned_number:
                output_data.append({'Number': int(cleaned_number), 'Name': cleaned_name})
                newly_processed_numbers.add(cleaned_number)
        if not output_data: return None
        
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                for number in newly_processed_numbers: f.write(f"{number}\n")
            print(f"Appended {len(newly_processed_numbers)} numbers to log.")
        except Exception as e:
            print(f"Error writing to log file: {e}")

        output_df = pd.DataFrame(output_data)
        
        # Save Excel file in the same directory as input file
        try:
            # If output_base_name is a full path, use its directory
            if os.path.isabs(output_base_name):
                output_dir = os.path.dirname(output_base_name)
                base_name = os.path.splitext(os.path.basename(output_base_name))[0]
            else:
                # Fallback to Documents folder for text processing
                output_dir = os.path.expanduser("~/Documents")
                base_name = output_base_name
            
            # Build output file path
            output_file_path = os.path.join(output_dir, f"{base_name}.xlsx")
            
            # Handle duplicate filenames
            counter = 1
            while os.path.exists(output_file_path):
                output_file_path = os.path.join(output_dir, f"{base_name}_{counter}.xlsx")
                counter += 1
            
            print(f"Saving Excel file to: {output_file_path}")
            logging.info(f"Saving Excel file to: {output_file_path}")
            
            # Save the Excel file
            output_df.to_excel(output_file_path, index=False, engine='openpyxl')
            
            # Verify file was created
            if os.path.exists(output_file_path):
                file_size = os.path.getsize(output_file_path)
                print(f"Excel file created successfully: {output_file_path} ({file_size} bytes)")
                logging.info(f"Excel file created successfully: {output_file_path} ({file_size} bytes)")
                return output_file_path
            else:
                print(f"Failed to create Excel file: {output_file_path}")
                logging.error(f"Failed to create Excel file: {output_file_path}")
                return None
                
        except Exception as e:
            print(f"Error saving Excel file: {e}")
            logging.error(f"Error saving Excel file: {e}", exc_info=True)
            return None
    
    def run_headless_process(self, vcf_file_path):
        print("--- Running in Headless Mode ---")
        unique_contacts, duplicate_contacts = self.get_unique_and_duplicate_contacts(vcf_file_path)
        if duplicate_contacts:
            print(f"Found {len(duplicate_contacts)} duplicates. GUI interaction is required.")
            return duplicate_contacts
        
        print("No duplicates found. Processing unique contacts automatically.")
        base, _ = os.path.splitext(vcf_file_path)
        output_file = self.process_and_save(unique_contacts, base)
        if output_file:
            print(f"Headless processing complete. Output saved to: {output_file}")
        else:
            print("No new contacts to process.")
        return None