#!/usr/bin/env python3
"""
Utility script to organize training data files.
This script helps organize training data files into the proper directory structure.
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path

def ensure_dir(directory):
    """Ensure a directory exists, creating it if necessary"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def copy_file(src, dst):
    """Copy a file from src to dst"""
    try:
        shutil.copy(src, dst)
        print(f"Copied: {src} → {dst}")
        return True
    except Exception as e:
        print(f"Error copying {src} to {dst}: {e}")
        return False

def validate_json(file_path):
    """Validate that a file is valid JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except json.JSONDecodeError:
        return False
    except Exception:
        return False

def organize_training_data(source_dir=None, target_dir="data/training"):
    """
    Organize training data files
    
    Args:
        source_dir: Directory containing source files (if None, use default locations)
        target_dir: Target directory for organized files
    """
    # Ensure target directory exists
    ensure_dir(target_dir)
    
    # Files to organize
    files_to_organize = [
        "custom_dataset_template.json",
        "promo_code_variations.json", 
        "common_variations.json",
        "synthetic_data_50.json"
    ]
    
    # Potential source locations
    source_locations = [
        "",  # root
        "data/",
        "data/custom/",
        "data/synthetic/"
    ]
    
    # If source_dir is provided, use it
    if source_dir:
        source_locations = [source_dir]
    
    # Keep track of organized files
    organized_files = []
    
    # Copy files
    for file_name in files_to_organize:
        file_found = False
        
        for source_loc in source_locations:
            source_path = os.path.join(source_loc, file_name)
            
            if os.path.exists(source_path) and validate_json(source_path):
                target_path = os.path.join(target_dir, file_name)
                if copy_file(source_path, target_path):
                    organized_files.append(file_name)
                    file_found = True
                    break
        
        if not file_found:
            print(f"Warning: Could not find valid JSON file: {file_name}")
    
    # Print summary
    print("\nOrganization Summary:")
    print(f"Organized {len(organized_files)} training data files to {target_dir}/")
    
    for file in organized_files:
        print(f"✓ {file}")
    
    for file in set(files_to_organize) - set(organized_files):
        print(f"✗ {file} (not found or invalid)")
    
    # Copy or create README
    readme_src = "data/training-readme.md"
    readme_dst = os.path.join(target_dir, "README.md")
    
    if os.path.exists(readme_src):
        copy_file(readme_src, readme_dst)
    else:
        print(f"Warning: README file not found at {readme_src}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Organize training data files')
    parser.add_argument('--source', help='Source directory containing training files')
    parser.add_argument('--target', default='data/training', help='Target directory for organized files')
    
    args = parser.parse_args()
    
    print("🔍 Organizing training data files...")
    organize_training_data(args.source, args.target)
    print("✅ Organization complete!")

if __name__ == "__main__":
    main() 