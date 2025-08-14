#!/usr/bin/env python3
"""
Test script to verify VCF processing functionality
Run this to test if VCF files are being processed correctly
"""

import os
import sys
import logging
from vcf_extractor import VCFProcessor

def test_vcf_processing():
    """Test VCF processing with a sample file"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Find a VCF file to test with
    vcf_files = [f for f in os.listdir('.') if f.endswith('.vcf')]
    
    if not vcf_files:
        print("No VCF files found in current directory")
        return False
    
    vcf_file = vcf_files[0]
    print(f"Testing with VCF file: {vcf_file}")
    
    # Create processor
    log_file = "test_processing.log"
    processor = VCFProcessor(log_file_path=log_file)
    
    # Test VCF reading
    print("\n=== Testing VCF Reading ===")
    vcf_content = processor._read_vcf(vcf_file)
    
    if vcf_content is None:
        print("❌ Failed to read VCF file")
        return False
    
    print(f"✅ VCF file read successfully. Content length: {len(vcf_content)}")
    print(f"First 200 characters: {vcf_content[:200]}...")
    
    # Test contact extraction
    print("\n=== Testing Contact Extraction ===")
    contacts = processor._extract_contact_data(vcf_content)
    
    if not contacts:
        print("❌ No contacts extracted from VCF")
        return False
    
    print(f"✅ Extracted {len(contacts)} contacts")
    for i, contact in enumerate(contacts[:5]):  # Show first 5
        print(f"  {i+1}. {contact['name']} -> {contact['number']}")
    
    # Test full processing
    print("\n=== Testing Full Processing ===")
    unique_contacts, duplicate_contacts = processor.get_unique_and_duplicate_contacts(vcf_file)
    
    print(f"✅ Processing complete:")
    print(f"  - Unique contacts: {len(unique_contacts)}")
    print(f"  - Duplicate contacts: {len(duplicate_contacts)}")
    
    # Test Excel output
    if unique_contacts:
        print("\n=== Testing Excel Output ===")
        output_file = processor.process_and_save(unique_contacts[:3], "test_output")
        if output_file:
            print(f"✅ Excel file created: {output_file}")
        else:
            print("❌ Failed to create Excel file")
            return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    success = test_vcf_processing()
    sys.exit(0 if success else 1)