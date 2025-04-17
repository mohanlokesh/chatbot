#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import yaml
import logging
import glob
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional

# Import the conflict checker
from check_rasa_conflicts import (
    ConflictChecker, 
    RASA_DIR, DATA_DIR, DOMAIN_PATH, NLU_PATH, 
    STORIES_PATH, RULES_PATH, ACTIONS_PATH, CONFIG_PATH
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rasa_fixes.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RasaConflictFixer")

# Configuration paths
RASA_DIR = "."
DATA_DIR = os.path.join(RASA_DIR, "data")
DOMAIN_PATH = os.path.join(RASA_DIR, "domain.yml")
NLU_PATH = os.path.join(DATA_DIR, "nlu.yml")
STORIES_PATH = os.path.join(DATA_DIR, "stories.yml")
RULES_PATH = os.path.join(DATA_DIR, "rules.yml")
ACTIONS_PATH = os.path.join(RASA_DIR, "actions.py")
CONFIG_PATH = os.path.join(RASA_DIR, "config.yml")

# Directory for backups
BACKUP_DIR = os.path.join(RASA_DIR, "rasa_backups")


class ConflictFixer:
    """
    A utility to fix configuration conflicts and inconsistencies in Rasa projects
    detected by check_rasa_conflicts.py.
    """
    
    def __init__(self):
        self.domain_data = {}
        self.nlu_data = {}
        self.stories_data = {}
        self.rules_data = {}
        self.config_data = {}
        self.fixes_count = 0
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            logger.info(f"Created backup directory: {BACKUP_DIR}")
        
        # Load all YAML files
        self._load_all_files()
    
    def _load_yaml(self, file_path: str) -> Dict:
        """
        Load a YAML file and return its contents as a dictionary.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the YAML content or empty dict if file doesn't exist
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File {file_path} does not exist")
                return {}
                
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {str(e)}")
            return {}
    
    def _save_yaml(self, data: Dict, file_path: str) -> bool:
        """
        Save dictionary as YAML to the specified file path.
        Creates a backup of the original file first.
        
        Args:
            data: Dictionary to save
            file_path: Path to save the YAML file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if file exists
            if os.path.exists(file_path):
                backup_filename = os.path.basename(file_path) + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = os.path.join(BACKUP_DIR, backup_filename)
                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
                
            # Save updated file
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"Updated file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {file_path}: {str(e)}")
            return False
    
    def _load_all_files(self) -> None:
        """Load all required Rasa configuration files."""
        self.domain_data = self._load_yaml(DOMAIN_PATH)
        self.nlu_data = self._load_yaml(NLU_PATH)
        self.stories_data = self._load_yaml(STORIES_PATH)
        self.rules_data = self._load_yaml(RULES_PATH)
        self.config_data = self._load_yaml(CONFIG_PATH)
    
    def fix_missing_intents(self) -> int:
        """
        Fix intents that are defined in NLU but missing in domain, or vice versa.
        
        Returns:
            Number of fixes made
        """
        fixes_count = 0
        
        # Extract intents from domain and NLU
        domain_intents = set(self.domain_data.get('intents', []))
        
        nlu_intents = set()
        for example in self.nlu_data.get('nlu', []):
            if example.get('intent'):
                nlu_intents.add(example.get('intent'))
        
        # Add intents from NLU to domain
        missing_in_domain = nlu_intents - domain_intents
        if missing_in_domain:
            fixes_count += len(missing_in_domain)
            
            # Initialize intents list if needed
            if 'intents' not in self.domain_data:
                self.domain_data['intents'] = []
            
            # Add missing intents to domain
            self.domain_data['intents'].extend(list(missing_in_domain))
            logger.info(f"Added {len(missing_in_domain)} missing intents to domain: {', '.join(missing_in_domain)}")
            
            # Save updated domain
            self._save_yaml(self.domain_data, DOMAIN_PATH)
        
        # Add intents from domain to NLU with placeholder examples
        missing_in_nlu = domain_intents - nlu_intents
        if missing_in_nlu:
            fixes_count += len(missing_in_nlu)
            
            # Initialize nlu list if needed
            if 'nlu' not in self.nlu_data:
                self.nlu_data['nlu'] = []
            
            # Add missing intents to NLU
            for intent in missing_in_nlu:
                self.nlu_data['nlu'].append({
                    'intent': intent,
                    'examples': f"- TODO: Add examples for {intent}\n"
                })
            
            logger.info(f"Added {len(missing_in_nlu)} missing intents to NLU with placeholder examples: {', '.join(missing_in_nlu)}")
            
            # Save updated NLU
            self._save_yaml(self.nlu_data, NLU_PATH)
        
        return fixes_count
    
    def fix_undefined_actions(self) -> int:
        """
        Fix actions that are used in stories/rules but not defined in domain
        or create templates for custom actions without implementation.
        
        Returns:
            Number of fixes made
        """
        fixes_count = 0
        
        # Extract actions from domain and stories/rules
        domain_actions = set(self.domain_data.get('actions', []))
        
        story_actions = set()
        for story in self.stories_data.get('stories', []):
            for step in story.get('steps', []):
                if 'action' in step:
                    story_actions.add(step['action'])
        
        for rule in self.rules_data.get('rules', []):
            for step in rule.get('steps', []):
                if 'action' in step:
                    story_actions.add(step['action'])
        
        # Add actions from stories/rules to domain
        missing_in_domain = story_actions - domain_actions
        missing_in_domain = {action for action in missing_in_domain if not action.startswith('utter_')}
        
        if missing_in_domain:
            fixes_count += len(missing_in_domain)
            
            # Initialize actions list if needed
            if 'actions' not in self.domain_data:
                self.domain_data['actions'] = []
            
            # Add missing actions to domain
            self.domain_data['actions'].extend(list(missing_in_domain))
            logger.info(f"Added {len(missing_in_domain)} missing actions to domain: {', '.join(missing_in_domain)}")
            
            # Save updated domain
            self._save_yaml(self.domain_data, DOMAIN_PATH)
        
        # Create templates for custom actions without implementation
        custom_actions = {action for action in domain_actions if action.startswith('action_') and not action == 'action_restart'}
        missing_implementations = set()
        
        if os.path.exists(ACTIONS_PATH):
            with open(ACTIONS_PATH, 'r', encoding='utf-8') as f:
                actions_content = f.read()
            
            for action in custom_actions:
                class_name = 'class ' + ''.join(word.capitalize() for word in action.split('_')) + '('
                if class_name not in actions_content:
                    missing_implementations.add(action)
        
        if missing_implementations:
            fixes_count += len(missing_implementations)
            
            # Create backup of actions.py
            backup_filename = os.path.basename(ACTIONS_PATH) + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            
            if os.path.exists(ACTIONS_PATH):
                shutil.copy2(ACTIONS_PATH, backup_path)
                logger.info(f"Created backup: {backup_path}")
                
                # Append action implementations
                with open(ACTIONS_PATH, 'a', encoding='utf-8') as f:
                    f.write("\n\n# Auto-generated action implementations\n")
                    
                    for action in missing_implementations:
                        class_name = ''.join(word.capitalize() for word in action.split('_'))
                        f.write(f"""
class {class_name}(Action):
    def name(self) -> Text:
        return "{action}"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # TODO: Implement action logic here
        dispatcher.utter_message(text="Action {action} executed")
        return []
""")
            else:
                # Create new actions.py file
                with open(ACTIONS_PATH, 'w', encoding='utf-8') as f:
                    f.write("""# This file contains the custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

""")
                    
                    for action in missing_implementations:
                        class_name = ''.join(word.capitalize() for word in action.split('_'))
                        f.write(f"""
class {class_name}(Action):
    def name(self) -> Text:
        return "{action}"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # TODO: Implement action logic here
        dispatcher.utter_message(text="Action {action} executed")
        return []
""")
            
            logger.info(f"Added {len(missing_implementations)} missing action implementations to {ACTIONS_PATH}")
        
        return fixes_count
    
    def fix_missing_entities(self) -> int:
        """
        Fix entities that are used in NLU but not defined in domain.
        
        Returns:
            Number of fixes made
        """
        fixes_count = 0
        
        # Extract entities from domain and NLU
        domain_entities = set(self.domain_data.get('entities', []))
        
        nlu_entities = set()
        for example in self.nlu_data.get('nlu', []):
            if 'examples' in example:
                entity_pattern = r'\[.*?\]\((\w+)\)'
                for match in re.finditer(entity_pattern, example['examples']):
                    nlu_entities.add(match.group(1))
        
        # Add entities from NLU to domain
        missing_in_domain = nlu_entities - domain_entities
        if missing_in_domain:
            fixes_count += len(missing_in_domain)
            
            # Initialize entities list if needed
            if 'entities' not in self.domain_data:
                self.domain_data['entities'] = []
            
            # Add missing entities to domain
            self.domain_data['entities'].extend(list(missing_in_domain))
            logger.info(f"Added {len(missing_in_domain)} missing entities to domain: {', '.join(missing_in_domain)}")
            
            # Save updated domain
            self._save_yaml(self.domain_data, DOMAIN_PATH)
        
        return fixes_count
    
    def fix_missing_slots(self) -> int:
        """
        Fix slots that are mentioned in stories/rules but not defined in domain.
        
        Returns:
            Number of fixes made
        """
        fixes_count = 0
        
        # Extract slots from domain and stories/rules
        domain_slots = set(self.domain_data.get('slots', {}).keys())
        
        story_slots = set()
        
        # Check stories
        for story in self.stories_data.get('stories', []):
            for step in story.get('steps', []):
                if 'slot_was_set' in step:
                    for slot_item in step['slot_was_set']:
                        if isinstance(slot_item, dict):
                            story_slots.update(slot_item.keys())
                        else:
                            story_slots.add(slot_item)
        
        # Check rules
        for rule in self.rules_data.get('rules', []):
            for step in rule.get('steps', []):
                if 'slot_was_set' in step:
                    for slot_item in step['slot_was_set']:
                        if isinstance(slot_item, dict):
                            story_slots.update(slot_item.keys())
                        else:
                            story_slots.add(slot_item)
        
        # Add slots from stories/rules to domain
        missing_in_domain = story_slots - domain_slots
        if missing_in_domain:
            fixes_count += len(missing_in_domain)
            
            # Initialize slots dict if needed
            if 'slots' not in self.domain_data:
                self.domain_data['slots'] = {}
            
            # Add missing slots to domain
            for slot in missing_in_domain:
                self.domain_data['slots'][slot] = {
                    'type': 'text',  # Default type
                    'influence_conversation': True
                }
            
            logger.info(f"Added {len(missing_in_domain)} missing slots to domain: {', '.join(missing_in_domain)}")
            
            # Save updated domain
            self._save_yaml(self.domain_data, DOMAIN_PATH)
        
        return fixes_count
    
    def fix_regex_configuration(self) -> int:
        """
        Fix RegexEntityExtractor configuration when regex features are used.
        
        Returns:
            Number of fixes made
        """
        fixes_count = 0
        
        # Check if regex features are defined in NLU
        has_regex = False
        for item in self.nlu_data.get('nlu', []):
            if 'regex' in item:
                has_regex = True
                break
        
        if has_regex:
            # Check if RegexEntityExtractor is in pipeline
            pipeline = self.config_data.get('pipeline', [])
            has_regex_extractor = False
            
            for component in pipeline:
                if isinstance(component, dict) and component.get('name') == 'RegexEntityExtractor':
                    has_regex_extractor = True
                    break
                elif isinstance(component, str) and component == 'RegexEntityExtractor':
                    has_regex_extractor = True
                    break
            
            if not has_regex_extractor:
                fixes_count += 1
                
                # Add RegexEntityExtractor to pipeline
                if not pipeline:
                    # Initialize pipeline if needed
                    self.config_data['pipeline'] = [{'name': 'RegexEntityExtractor'}]
                else:
                    # Find appropriate position to insert
                    # Add after entity extractors but before featurizers if possible
                    inserted = False
                    for i, component in enumerate(pipeline):
                        component_name = component if isinstance(component, str) else component.get('name', '')
                        if 'EntityExtractor' in component_name and 'Regex' not in component_name:
                            pipeline.insert(i + 1, {'name': 'RegexEntityExtractor'})
                            inserted = True
                            break
                    
                    if not inserted:
                        # Just append to the end of the pipeline
                        pipeline.append({'name': 'RegexEntityExtractor'})
                
                logger.info("Added RegexEntityExtractor to the pipeline")
                
                # Save updated config
                self._save_yaml(self.config_data, CONFIG_PATH)
        
        return fixes_count
    
    def create_utterance_templates(self) -> int:
        """
        Create missing utterance templates for actions that start with 'utter_'
        but don't have a corresponding response in the domain.
        
        Returns:
            Number of fixes made
        """
        fixes_count = 0
        
        # Extract all utter_ actions from stories/rules and responses
        utter_actions = set()
        
        # From stories
        for story in self.stories_data.get('stories', []):
            for step in story.get('steps', []):
                if 'action' in step and step['action'].startswith('utter_'):
                    utter_actions.add(step['action'])
        
        # From rules
        for rule in self.rules_data.get('rules', []):
            for step in rule.get('steps', []):
                if 'action' in step and step['action'].startswith('utter_'):
                    utter_actions.add(step['action'])
        
        # Existing responses
        responses = self.domain_data.get('responses', {})
        existing_responses = set(responses.keys())
        
        # Find missing responses
        missing_responses = utter_actions - existing_responses
        
        if missing_responses:
            fixes_count += len(missing_responses)
            
            # Initialize responses dict if needed
            if 'responses' not in self.domain_data:
                self.domain_data['responses'] = {}
            
            # Add missing responses
            for action in missing_responses:
                self.domain_data['responses'][action] = [
                    {'text': f"TODO: Add response for {action}"}
                ]
            
            logger.info(f"Created {len(missing_responses)} missing utterance templates: {', '.join(missing_responses)}")
            
            # Save updated domain
            self._save_yaml(self.domain_data, DOMAIN_PATH)
        
        return fixes_count
    
    def run_all_fixes(self) -> int:
        """
        Run all conflict fixes and return the total number of fixes made.
        
        Returns:
            Total number of fixes made
        """
        logger.info("Starting Rasa conflict fixes...")
        
        self.fixes_count = 0
        
        # Run all fixes
        self.fixes_count += self.fix_missing_intents()
        self.fixes_count += self.fix_undefined_actions()
        self.fixes_count += self.fix_missing_entities()
        self.fixes_count += self.fix_missing_slots()
        self.fixes_count += self.fix_regex_configuration()
        self.fixes_count += self.create_utterance_templates()
        
        logger.info(f"Completed Rasa conflict fixes: made {self.fixes_count} fixes")
        
        return self.fixes_count


def main():
    """Run the Rasa conflict fixer."""
    try:
        fixer = ConflictFixer()
        fixes_count = fixer.run_all_fixes()
        
        print(f"\nSummary: Applied {fixes_count} fixes to your Rasa project.")
        
        if fixes_count > 0:
            print("\nBackups of modified files were created in the 'rasa_backups' directory.")
            print("\nNext steps:")
            print("1. Review the changes and adjust as needed")
            print("2. Train your model with: python -m rasa train")
            print("3. Run the conflict checker again to verify: python check_rasa_conflicts.py")
        
        return 0
    except Exception as e:
        logger.error(f"Error during conflict fixing: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 