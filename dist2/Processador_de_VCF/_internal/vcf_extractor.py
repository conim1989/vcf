# vcf_extractor.py

import io
import os
import re
import pandas as pd
from unidecode import unidecode
from config import TITLES_TO_REMOVE

class VCFProcessor:
    def __init__(self, log_file_path, titles_to_remove):
        import os
        # Ensure log_file_path is absolute path
        if not os.path.isabs(log_file_path):
            log_file_path = os.path.abspath(log_file_path)
        self.log_file_path = log_file_path
        if titles_to_remove:
            self.title_pattern = r'\b(' + '|'.join(re.escape(title) for title in titles_to_remove) + r')\.?\b'
            self.title_regex = re.compile(self.title_pattern, re.IGNORECASE)
        else:
            self.title_regex = None
        self.processed_numbers_log = self._read_log()

    def _read_vcf(self, vcf_file_path):
        try:
            with io.open(vcf_file_path, 'r', encoding='utf-8') as f: return f.read()
        except UnicodeDecodeError:
            with io.open(vcf_file_path, 'r', encoding='iso-8859-1') as f: return f.read()
        except Exception as e:
            print(f"Error reading VCF file: {e}")
            return None

    def _extract_contact_data(self, vcf_content):
        """
        A faithful Python translation of the VBA macro's logic for extracting
        contact names and WAIDs.
        """
        contacts = []
        # Split the VCF content into individual contact blocks
        vcard_blocks = vcf_content.split("BEGIN:VCARD")
        
        print(f"Starting contact data extraction from {len(vcard_blocks) - 1} VCF blocks.")

        for block in vcard_blocks:
            if "END:VCARD" not in block:
                continue

            name = None
            waid = None

            # Search for FN (Full Name) within the block
            fn_match = re.search(r'FN:(.*)', block)
            if fn_match:
                name = fn_match.group(1).strip()

            # Search for all TEL lines to find the WAID
            tel_lines = re.findall(r'TEL;.*', block)
            for tel_line in tel_lines:
                waid_match = re.search(r'waid=([^:]+):', tel_line)
                if waid_match:
                    waid = waid_match.group(1).strip()
                    break # Found the WAID, no need to check other TEL lines for this contact

            if name and waid:
                contacts.append({'name': name, 'number': waid})

        print(f"Finished contact data extraction. Found {len(contacts)} contacts with names and WAIDs.")
        return contacts

    def _clean_name(self, name):
        """
        Faithfully translates the VBA logic with advanced character normalization.
        """
        if not name: return ""
        
        # 1. Transliterate Unicode to plain ASCII (e.g., "𝗟𝗶𝗹𝗶𝗔𝗻𝗮 🌻" -> "LiliAna ?")
        ascii_name = unidecode(name)
        
        # 2. Remove any remaining non-alphanumeric, non-space characters
        cleaned_name = re.sub(r'[^a-zA-Z0-9\s]+', '', ascii_name)
        
        # 3. Remove titles (case-insensitive, with optional period)
        if self.title_regex:
            cleaned_name = self.title_regex.sub('', cleaned_name)
            
        # 4. Remove extra spaces
        cleaned_name = ' '.join(cleaned_name.split())
        
        # 5. Keep only the first word and title case it
        words = cleaned_name.split()
        return words[0].title() if words else ""

    def _clean_phone_number(self, number):
        return re.sub(r'\D', '', number) if number else ""

    def _read_log(self):
        """Reads the log from a simple, fast text file."""
        processed_numbers = set()
        if os.path.exists(self.log_file_path):
            try:
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # No need to clean, we will store cleaned numbers
                        processed_numbers.add(line.strip())
                print(f"Loaded {len(processed_numbers)} processed numbers from log.")
            except Exception as e:
                print(f"Error reading log file '{self.log_file_path}': {e}")
        return processed_numbers

    def remove_from_log(self, numbers_to_remove):
        """Removes numbers from the text log file."""
        if not os.path.exists(self.log_file_path) or not numbers_to_remove: return
        # Read all lines, filter out the ones to remove, and write back
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line.strip() not in numbers_to_remove:
                    f.write(line)
        print(f"Removed {len(numbers_to_remove)} numbers from the log.")
        self.processed_numbers_log = self._read_log()

    def get_unique_and_duplicate_contacts(self, vcf_file_path):
        vcf_content = self._read_vcf(vcf_file_path)
        if vcf_content is None: return [], []
        
        extracted_contacts = self._extract_contact_data(vcf_content)
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

    def process_and_save(self, vcf_file_path, contacts_to_process):
        if not contacts_to_process: return None
        output_data, newly_processed_numbers = [], set()
        for contact in contacts_to_process:
            cleaned_number = contact['cleaned_number']
            
            cleaned_name = self._clean_name(contact['original_name'])
            if cleaned_number:
                output_data.append({'Number': int(cleaned_number), 'Name': cleaned_name})
                newly_processed_numbers.add(int(cleaned_number))
        if not output_data: return None
        
        # Append new numbers to the text log file
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                for number in newly_processed_numbers:
                    f.write(f"{number}\n")
            print(f"Appended {len(newly_processed_numbers)} numbers to log.")
        except Exception as e:
            print(f"Error writing to log file: {e}")

        # Saving to XLSX is still done with pandas, but only at the end
        output_df = pd.DataFrame(output_data)
        base, ext = os.path.splitext(vcf_file_path)
        output_file_path = f"{base}.xlsx"
        counter = 1
        while os.path.exists(output_file_path):
            output_file_path = f"{base}_{counter}.xlsx"; counter += 1
        output_df.to_excel(output_file_path, index=False, engine='openpyxl')
        return output_file_path
    
    def run_headless_process(self, vcf_file_path):
        """
        Runs the entire process non-interactively. Processes only unique contacts.
        Returns the list of duplicates if any are found, otherwise returns None.
        """
        print("--- Running in Headless Mode ---")
        unique_contacts, duplicate_contacts = self.get_unique_and_duplicate_contacts(vcf_file_path)

        if duplicate_contacts:
            print(f"Found {len(duplicate_contacts)} duplicates. GUI interaction is required.")
            # Return the duplicates so the main app can decide to show the GUI
            return duplicate_contacts
        
        # If no duplicates, process only the unique contacts and finish
        print("No duplicates found. Processing unique contacts automatically.")
        output_file = self.process_and_save(vcf_file_path, unique_contacts)
        if output_file:
            print(f"Headless processing complete. Output saved to: {output_file}")
        else:
            print("No new contacts to process.")
        
        # Return None to indicate that no GUI interaction is needed
        return None