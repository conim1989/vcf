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

def read_titles_from_config_ini():
    if getattr(sys, 'frozen', False):
        config_ini_path = os.path.join(sys._MEIPASS, 'config.ini')
    else:
        config_ini_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_ini_path)
    titles_str = config.get('Titles', 'titles_to_remove', fallback='[]')
    try:
        titles = json.loads(titles_str.replace("'", '"'))
    except Exception:
        try:
            titles = ast.literal_eval(titles_str)
        except Exception:
            titles = []
    return titles

class VCFProcessor:
    def __init__(self, log_file_path, titles_to_remove=None):
        import os
        if not os.path.isabs(log_file_path):
            log_file_path = os.path.abspath(log_file_path)
        self.log_file_path = log_file_path
        if titles_to_remove is None:
            # <<< CORRIGIDO >>> Usar a função global apenas como fallback
            titles_to_remove = read_titles_from_config_ini()
        if titles_to_remove:
            self.title_pattern = r'\b(' + '|'.join(re.escape(title) for title in titles_to_remove) + r')\.?\b'
            self.title_regex = re.compile(self.title_pattern, re.IGNORECASE)
        else:
            self.title_regex = None
        self.processed_numbers_log = self._read_log()

    def _read_vcf(self, vcf_file_path):
        # <<< ALTERAÇÃO 1: LOGGING DETALHADO >>>
        try:
            logging.info(f"Tentando ler o arquivo VCF: {vcf_file_path} com encoding utf-8.")
            with io.open(vcf_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logging.info(f"Arquivo lido com sucesso (UTF-8). Tamanho: {len(content)} caracteres.")
            return content
        except UnicodeDecodeError:
            try:
                logging.warning(f"Falha no UTF-8. Tentando com encoding iso-8859-1.")
                with io.open(vcf_file_path, 'r', encoding='iso-8859-1') as f:
                    content = f.read()
                logging.info(f"Arquivo lido com sucesso (ISO-8859-1). Tamanho: {len(content)} caracteres.")
                return content
            except Exception as e:
                logging.error(f"ERRO CRÍTICO ao ler o arquivo VCF com ISO-8859-1: {e}", exc_info=True)
                print(f"Error reading VCF file (iso-8859-1): {e}")
                return None
        except Exception as e:
            logging.error(f"ERRO CRÍTICO ao ler o arquivo VCF: {e}", exc_info=True)
            print(f"Error reading VCF file: {e}")
            return None

    def _extract_contact_data(self, vcf_content):
        """Extract contact data from VCF content with enhanced error handling"""
        contacts = []
        
        # Split into VCF blocks
        vcard_blocks = vcf_content.split("BEGIN:VCARD")
        
        # Debug logging
        logging.info(f"Processing {len(vcard_blocks) - 1} VCF blocks")
        
        for block in vcard_blocks:
            if "END:VCARD" not in block:
                continue
                
            name, waid = None, None
            
            # Extract name
            fn_match = re.search(r'FN:(.*)', block)
            if fn_match:
                name = fn_match.group(1).strip()
            
            # Extract phone number and WAID
            tel_lines = re.findall(r'TEL;.*', block)
            for tel_line in tel_lines:
                # Look for WAID in TEL lines
                waid_match = re.search(r'waid=([^:]+):', tel_line)
                if waid_match:
                    waid = waid_match.group(1).strip()
                    break
                else:
                    # Fallback to just the phone number
                    phone_match = re.search(r'TEL;[^:]*:(\+?\d+)', tel_line)
                    if phone_match:
                        waid = phone_match.group(1).strip()
                        break
            
            if name and waid:
                contacts.append({'name': name, 'number': waid})
        
        logging.info(f"Extracted {len(contacts)} contacts from VCF")
        return contacts

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
        
        # <<< ALTERAÇÃO 2: CORREÇÃO DO CAMINHO DE SAÍDA PARA O .EXE >>>
        # Determina o diretório de saída correto (ao lado do .exe ou do .py)
        if getattr(sys, 'frozen', False):
            output_dir = os.path.dirname(sys.executable)
        else:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Constrói o caminho completo do arquivo de saída
        output_file_path = os.path.join(output_dir, f"{output_base_name}.xlsx")
        
        counter = 1
        while os.path.exists(output_file_path):
            output_file_path = os.path.join(output_dir, f"{output_base_name}_{counter}.xlsx")
            counter += 1
            
        output_df.to_excel(output_file_path, index=False, engine='openpyxl')
        return output_file_path
    
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