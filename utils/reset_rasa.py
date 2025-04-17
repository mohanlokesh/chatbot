#!/usr/bin/env python3
"""
Rasa Reset and Initialization Script
------------------------------------
This script completely rebuilds a Rasa model from scratch:
1. Backs up existing Rasa files
2. Cleans all models and cache directories
3. Creates minimal training files
4. Trains a baseline model
5. Restores original files
6. Trains full model with conflict resolution
"""

import os
import sys
import shutil
import subprocess
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rasa_reset.log')
    ]
)
logger = logging.getLogger(__name__)

# Path configuration
RASA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rasa_bot")
BACKUP_DIR = os.path.join(os.path.dirname(RASA_DIR), "rasa_backup")
DATA_DIR = os.path.join(RASA_DIR, "data")
MODELS_DIR = os.path.join(RASA_DIR, "models")
ACTIONS_DIR = os.path.join(RASA_DIR, ".rasa", "cache", "action_server_actions")

# Essential files to backup
ESSENTIAL_FILES = [
    os.path.join(RASA_DIR, "domain.yml"),
    os.path.join(DATA_DIR, "nlu.yml"),
    os.path.join(DATA_DIR, "stories.yml"),
    os.path.join(DATA_DIR, "rules.yml"),
    os.path.join(RASA_DIR, "actions", "actions.py"),
    os.path.join(RASA_DIR, "config.yml"),
    os.path.join(RASA_DIR, "endpoints.yml"),
    os.path.join(RASA_DIR, "credentials.yml")
]

def run_command(command, cwd=None, capture_output=False):
    """Execute a shell command and handle errors."""
    try:
        logger.info(f"Running command: {command}")
        
        # Set shell to True for Windows compatibility
        is_windows = sys.platform.startswith('win')
        
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.stdout
        else:
            subprocess.run(
                command, 
                shell=True, 
                cwd=cwd,
                check=True
            )
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if capture_output:
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False

def backup_rasa_files():
    """Backup essential Rasa files before resetting."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}_{timestamp}"
    
    logger.info(f"Creating backup at {backup_path}")
    os.makedirs(backup_path, exist_ok=True)
    
    for file_path in ESSENTIAL_FILES:
        if os.path.exists(file_path):
            file_name = os.path.basename(file_path)
            dir_name = os.path.dirname(file_path).split(os.sep)[-1]
            
            # Create subdirectory for organization
            os.makedirs(os.path.join(backup_path, dir_name), exist_ok=True)
            backup_file = os.path.join(backup_path, dir_name, file_name)
            
            shutil.copy2(file_path, backup_file)
            logger.info(f"Backed up {file_path} to {backup_file}")
    
    return backup_path

def clean_rasa_environment():
    """Remove existing models and cache directories."""
    logger.info("Cleaning Rasa environment")
    
    # Remove models directory
    if os.path.exists(MODELS_DIR):
        shutil.rmtree(MODELS_DIR)
        logger.info(f"Removed {MODELS_DIR}")
    
    # Remove .rasa cache directory
    cache_dir = os.path.join(RASA_DIR, ".rasa")
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        logger.info(f"Removed {cache_dir}")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk(RASA_DIR):
        for dir in dirs:
            if dir == "__pycache__":
                pycache_dir = os.path.join(root, dir)
                shutil.rmtree(pycache_dir)
                logger.info(f"Removed {pycache_dir}")

def create_minimal_files():
    """Create minimal training files to ensure successful initial training."""
    logger.info("Creating minimal training files")
    
    # Create directory structure if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Minimal domain.yml
    minimal_domain = """version: "3.1"

intents:
  - greet
  - goodbye

responses:
  utter_greet:
  - text: "Hello! I am a bot."
  
  utter_goodbye:
  - text: "Goodbye!"

session_config:
  session_expiration_time: 60
  carry_over_slots_to_new_session: true
"""
    
    # Minimal nlu.yml
    minimal_nlu = """version: "3.1"

nlu:
- intent: greet
  examples: |
    - hello
    - hi
    - hey

- intent: goodbye
  examples: |
    - bye
    - goodbye
    - see you
"""
    
    # Minimal stories.yml
    minimal_stories = """version: "3.1"

stories:
- story: greet and goodbye
  steps:
  - intent: greet
  - action: utter_greet
  - intent: goodbye
  - action: utter_goodbye
"""
    
    # Minimal rules.yml
    minimal_rules = """version: "3.1"

rules:
- rule: Say goodbye when user says goodbye
  steps:
  - intent: goodbye
  - action: utter_goodbye
"""
    
    # Write minimal files
    with open(os.path.join(RASA_DIR, "domain.yml"), "w") as f:
        f.write(minimal_domain)
    
    with open(os.path.join(DATA_DIR, "nlu.yml"), "w") as f:
        f.write(minimal_nlu)
    
    with open(os.path.join(DATA_DIR, "stories.yml"), "w") as f:
        f.write(minimal_stories)
    
    with open(os.path.join(DATA_DIR, "rules.yml"), "w") as f:
        f.write(minimal_rules)
    
    logger.info("Created minimal training files")

def restore_original_files(backup_path, specific_files=None):
    """Restore original files from backup."""
    logger.info(f"Restoring original files from {backup_path}")
    
    files_to_restore = specific_files or ESSENTIAL_FILES
    
    for file_path in files_to_restore:
        if not os.path.exists(file_path):
            logger.warning(f"Original file path doesn't exist: {file_path}")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_name = os.path.basename(file_path)
        dir_name = os.path.dirname(file_path).split(os.sep)[-1]
        backup_file = os.path.join(backup_path, dir_name, file_name)
        
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, file_path)
            logger.info(f"Restored {backup_file} to {file_path}")
        else:
            logger.warning(f"Backup file not found: {backup_file}")

def fix_known_conflicts():
    """Fix known conflicts in training data."""
    logger.info("Fixing known conflicts in training data")
    
    # 1. Fix missing intent in domain.yml
    domain_path = os.path.join(RASA_DIR, "domain.yml")
    with open(domain_path, "r") as f:
        domain_content = f.read()
    
    # Add missing intents if needed
    if "ask_payments" not in domain_content:
        domain_content = domain_content.replace("intents:", "intents:\n  - ask_payments")
    
    with open(domain_path, "w") as f:
        f.write(domain_content)
    
    # 2. Fix stories.yml for consistent action handling
    stories_path = os.path.join(DATA_DIR, "stories.yml")
    with open(stories_path, "r") as f:
        stories_content = f.read()
    
    # Replace inconsistent action calls
    stories_content = stories_content.replace(
        "- intent: ask_payments\n  - action: utter_ask_payments",
        "- intent: ask_payments\n  - action: utter_ask_payment_methods"
    )
    
    with open(stories_path, "w") as f:
        f.write(stories_content)
    
    # 3. Add the missing intent to NLU if needed
    nlu_path = os.path.join(DATA_DIR, "nlu.yml")
    with open(nlu_path, "r") as f:
        nlu_content = f.read()
    
    if "- intent: ask_payments" not in nlu_content:
        payment_examples = """
- intent: ask_payments
  examples: |
    - How do I pay?
    - What are the payment options?
    - Payment methods available
    - How can I complete my payment?
    - Tell me about payment methods
"""
        # Add the missing intent to NLU
        nlu_content = nlu_content + payment_examples
        
        with open(nlu_path, "w") as f:
            f.write(nlu_content)
    
    logger.info("Fixed known conflicts in training data")

def train_rasa_model(model_name="model", minimal=False):
    """Train the Rasa model."""
    logger.info(f"Training Rasa model: {model_name} (minimal={minimal})")
    
    # Create models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Run Rasa train command
    train_cmd = f"rasa train --fixed-model-name={model_name}"
    
    if minimal:
        train_cmd += " --augmentation 0"
    
    success = run_command(train_cmd, cwd=RASA_DIR)
    
    if success:
        logger.info(f"Successfully trained model: {model_name}")
        return True
    else:
        logger.error(f"Failed to train model: {model_name}")
        return False

def main():
    """Main function to reset and initialize Rasa."""
    try:
        logger.info("Starting Rasa reset and initialization")
        
        # Step 1: Backup existing files
        backup_path = backup_rasa_files()
        
        # Step 2: Clean environment
        clean_rasa_environment()
        
        # Step 3: Create minimal files
        create_minimal_files()
        
        # Step 4: Train minimal model
        minimal_training_success = train_rasa_model(model_name="minimal_model", minimal=True)
        
        if not minimal_training_success:
            logger.error("Minimal model training failed. Exiting.")
            return False
        
        # Step 5: Restore original files
        restore_original_files(backup_path)
        
        # Step 6: Fix known conflicts
        fix_known_conflicts()
        
        # Step 7: Train full model
        full_training_success = train_rasa_model(model_name="model")
        
        if full_training_success:
            logger.info("Full model training successful!")
            logger.info("Rasa reset and initialization completed successfully")
            return True
        else:
            logger.error("Full model training failed.")
            logger.info("Restoring minimal model for basic functionality")
            
            # If full training fails, restore minimal model
            model_path = os.path.join(MODELS_DIR, "minimal_model.tar.gz")
            final_path = os.path.join(MODELS_DIR, "model.tar.gz")
            
            if os.path.exists(model_path):
                shutil.copy2(model_path, final_path)
                logger.info("Restored minimal model as the main model")
                return True
            else:
                logger.error("Could not restore minimal model")
                return False
            
    except Exception as e:
        logger.error(f"Error during Rasa reset: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 