#!/usr/bin/env python
"""
Script to set up the data directory structure for the chatbot
"""

import os
import sys
import shutil

def setup_data_directories():
    """Set up the data directory structure"""
    # Get the absolute project root path
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    
    # Define data directories to create
    data_dirs = [
        "data",
        "data/scraped",
        "data/scraped/ecommerce",
        "data/scraped/support", 
        "data/scraped/custom",
        "data/synthetic",
        "data/custom"
    ]
    
    # Create directories if they don't exist
    for directory in data_dirs:
        dir_path = os.path.join(PROJECT_ROOT, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {directory}")
    
    # Copy template file if it exists but not in the target directory
    template_source = os.path.join(PROJECT_ROOT, "data", "custom_dataset_template.json")
    template_target = os.path.join(PROJECT_ROOT, "data", "custom", "custom_dataset_template.json")
    
    if os.path.exists(template_source) and not os.path.exists(template_target):
        shutil.copy2(template_source, template_target)
        print(f"Copied template to: data/custom/")
    
    # Copy README if it exists but not in data/custom
    readme_source = os.path.join(PROJECT_ROOT, "data", "README.md")
    readme_target = os.path.join(PROJECT_ROOT, "data", "custom", "README.md")
    
    if os.path.exists(readme_source) and not os.path.exists(readme_target):
        shutil.copy2(readme_source, readme_target)
        print(f"Copied README to: data/custom/")
    
    print("\nData directory structure setup complete!")
    print("\nTo add training data to your chatbot, you can now use:")
    print("  python manual_dataset.py --all")
    print("  python auto_dataset.py --synthetic --add-synthetic")
    print("\nTo view data statistics:")
    print("  python train_chatbot.py --stats")

if __name__ == "__main__":
    setup_data_directories() 