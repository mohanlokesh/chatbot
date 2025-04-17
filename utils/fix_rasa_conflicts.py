#!/usr/bin/env python3
"""
Rasa Conflict Fixer
------------------
Automatically fixes common issues found by check_rasa_conflicts.py
"""

import os
import sys
import yaml
import re
import logging
import shutil
from typing import Dict, List, Set, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rasa_fixes.log')
    ]
)
logger = logging.getLogger(__name__)

# Path configuration
RASA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rasa_bot")
DATA_DIR = os.path.join(RASA_DIR, "data")
DOMAIN_PATH = os.path.join(RASA_DIR, "domain.yml")
NLU_PATH = os.path.join(DATA_DIR, "nlu.yml")
STORIES_PATH = os.path.join(DATA_DIR, "stories.yml")
RULES_PATH = os.path.join(DATA_DIR, "rules.yml")
ACTIONS_PATH = os.path.join(RASA_DIR, "actions", "actions.py")
CONFIG_PATH = os.path.join(RASA_DIR, "config.yml")

# Backup directory
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rasa_backups")

class ConflictFixer:
    """Class to fix conflicts in Rasa files."""
    
    def __init__(self):
        self.create_backups()
        
        # Load files
        self.domain = self._load_yaml(DOMAIN_PATH)
        self.nlu = self._load_yaml(NLU_PATH)
        self.stories = self._load_yaml(STORIES_PATH)
        self.rules = self._load_yaml(RULES_PATH)
        self.config = self._load_yaml(CONFIG_PATH)
        
        # Track fixes
        self.fixes = []
    
    def create_backups(self):
        """Create backups of original files."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        timestamp = self._get_timestamp()
        backup_subdir = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
        
        if not os.path.exists(backup_subdir):
            os.makedirs(backup_subdir)
            
            # Backup domain file
            if os.path.exists(DOMAIN_PATH):
                shutil.copy2(DOMAIN_PATH, os.path.join(backup_subdir, "domain.yml"))
            
            # Backup data directory
            data_backup_dir = os.path.join(backup_subdir, "data")
            if not os.path.exists(data_backup_dir):
                os.makedirs(data_backup_dir)
                
            if os.path.exists(NLU_PATH):
                shutil.copy2(NLU_PATH, os.path.join(data_backup_dir, "nlu.yml"))
                
            if os.path.exists(STORIES_PATH):
                shutil.copy2(STORIES_PATH, os.path.join(data_backup_dir, "stories.yml"))
                
            if os.path.exists(RULES_PATH):
                shutil.copy2(RULES_PATH, os.path.join(data_backup_dir, "rules.yml"))
                
            # Backup config
            if os.path.exists(CONFIG_PATH):
                shutil.copy2(CONFIG_PATH, os.path.join(backup_subdir, "config.yml"))
                
            # Backup actions
            actions_backup_dir = os.path.join(backup_subdir, "actions")
            if not os.path.exists(actions_backup_dir):
                os.makedirs(actions_backup_dir)
                
            if os.path.exists(ACTIONS_PATH):
                shutil.copy2(ACTIONS_PATH, os.path.join(actions_backup_dir, "actions.py"))
                
            logger.info(f"Created backup in {backup_subdir}")
        
        return backup_subdir
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string for backup folder naming."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_yaml(self, file_path: str) -> dict:
        """Load YAML file and return contents as dict."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = yaml.safe_load(file)
                return content or {}
            else:
                logger.warning(f"File not found: {file_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return {}
    
    def _save_yaml(self, file_path: str, content: Dict) -> bool:
        """Save dict as YAML to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(content, file, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved changes to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
            return False
    
    def fix_missing_intents(self):
        """Add missing intents to domain.yml or nlu.yml."""
        # Collect intents from all files
        domain_intents = set(self.domain.get('intents', []))
        
        nlu_intents = set()
        if self.nlu and 'nlu' in self.nlu:
            for item in self.nlu['nlu']:
                if 'intent' in item:
                    nlu_intents.add(item['intent'])
        
        story_intents = set()
        if self.stories and 'stories' in self.stories:
            for story in self.stories['stories']:
                if 'steps' in story:
                    for step in story['steps']:
                        if 'intent' in step:
                            story_intents.add(step['intent'])
        
        if self.rules and 'rules' in self.rules:
            for rule in self.rules['rules']:
                if 'steps' in rule:
                    for step in rule['steps']:
                        if 'intent' in step:
                            story_intents.add(step['intent'])
        
        # Fix intents in domain
        intents_to_add_to_domain = (nlu_intents | story_intents) - domain_intents
        if intents_to_add_to_domain:
            if 'intents' not in self.domain:
                self.domain['intents'] = []
            
            for intent in intents_to_add_to_domain:
                self.domain['intents'].append(intent)
                self.fixes.append(f"Added missing intent '{intent}' to domain.yml")
            
            self._save_yaml(DOMAIN_PATH, self.domain)
        
        # Fix intents in NLU
        intents_to_add_to_nlu = (domain_intents | story_intents) - nlu_intents
        if intents_to_add_to_nlu:
            if 'nlu' not in self.nlu:
                self.nlu['nlu'] = []
            
            for intent in intents_to_add_to_nlu:
                # Create minimal example for each intent
                self.nlu['nlu'].append({
                    'intent': intent,
                    'examples': f"- {intent} placeholder\n- another {intent} example"
                })
                self.fixes.append(f"Added missing intent '{intent}' to nlu.yml with placeholder examples")
            
            self._save_yaml(NLU_PATH, self.nlu)
    
    def fix_undefined_actions(self):
        """Add missing actions to domain.yml."""
        # Collect actions from stories and rules
        story_actions = set()
        if self.stories and 'stories' in self.stories:
            for story in self.stories['stories']:
                if 'steps' in story:
                    for step in story['steps']:
                        if 'action' in step:
                            story_actions.add(step['action'])
        
        if self.rules and 'rules' in self.rules:
            for rule in self.rules['rules']:
                if 'steps' in rule:
                    for step in rule['steps']:
                        if 'action' in step:
                            story_actions.add(step['action'])
        
        # Get actions from domain
        domain_actions = set(self.domain.get('actions', []))
        domain_responses = set(self.domain.get('responses', {}).keys())
        all_defined_actions = domain_actions | domain_responses
        
        # Filter default actions
        default_actions = {'action_listen', 'action_restart', 'action_default_fallback', 'action_session_start', 'action_back'}
        actions_to_add = {action for action in story_actions 
                        if action not in all_defined_actions 
                        and action not in default_actions
                        and not (action.startswith('utter_') and action in domain_responses)}
        
        if actions_to_add:
            if 'actions' not in self.domain:
                self.domain['actions'] = []
            
            for action in actions_to_add:
                # If it's an utter response, add it to responses
                if action.startswith('utter_') and action not in domain_responses:
                    if 'responses' not in self.domain:
                        self.domain['responses'] = {}
                    
                    self.domain['responses'][action] = [
                        {"text": f"Placeholder response for {action}"}
                    ]
                    self.fixes.append(f"Added missing response '{action}' to domain.yml")
                else:
                    # Otherwise add to actions
                    self.domain['actions'].append(action)
                    self.fixes.append(f"Added missing action '{action}' to domain.yml")
            
            self._save_yaml(DOMAIN_PATH, self.domain)
            
            # Also create action stubs if they don't exist
            self._create_missing_action_stubs(actions_to_add)
    
    def _create_missing_action_stubs(self, actions: Set[str]):
        """Create stub implementations for missing custom actions."""
        # Only create stubs for true custom actions (not utterances or default actions)
        custom_actions = {action for action in actions 
                         if not action.startswith('utter_') 
                         and not action.startswith('action_default')
                         and not action in {'action_listen', 'action_restart', 'action_back', 'action_session_start'}}
        
        if not custom_actions:
            return
            
        if not os.path.exists(os.path.dirname(ACTIONS_PATH)):
            os.makedirs(os.path.dirname(ACTIONS_PATH))
        
        # Read existing actions.py if it exists
        existing_content = ""
        if os.path.exists(ACTIONS_PATH):
            with open(ACTIONS_PATH, 'r', encoding='utf-8') as file:
                existing_content = file.read()
        else:
            # Create a new actions.py with basic imports
            existing_content = """from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

"""
        
        # Add each missing action
        for action in custom_actions:
            # Check if the action class already exists
            class_name = ''.join(word.capitalize() for word in action.split('_'))
            if f"class {class_name}" not in existing_content and f"return '{action}'" not in existing_content:
                new_action = f"""
class {class_name}(Action):
    def name(self) -> Text:
        return "{action}"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # TODO: Implement {action} logic
        dispatcher.utter_message(text="Action {action} executed")
        
        return []
"""
                existing_content += new_action
                self.fixes.append(f"Created stub implementation for action '{action}' in actions.py")
        
        # Save the updated actions.py
        with open(ACTIONS_PATH, 'w', encoding='utf-8') as file:
            file.write(existing_content)
    
    def fix_missing_entities(self):
        """Add missing entities to domain.yml."""
        # Extract entities from NLU examples
        nlu_entities = set()
        if self.nlu and 'nlu' in self.nlu:
            for item in self.nlu['nlu']:
                if 'examples' in item:
                    examples = item['examples']
                    if isinstance(examples, str):
                        # Find entities in format [entity_value](entity_name)
                        entity_pattern = r'\[.+?\]\((.+?)\)'
                        nlu_entities.update(re.findall(entity_pattern, examples))
        
        # Get entities from domain
        domain_entities = set(self.domain.get('entities', []))
        
        # Add missing entities to domain
        entities_to_add = nlu_entities - domain_entities
        if entities_to_add:
            if 'entities' not in self.domain:
                self.domain['entities'] = []
            
            for entity in entities_to_add:
                self.domain['entities'].append(entity)
                self.fixes.append(f"Added missing entity '{entity}' to domain.yml")
            
            self._save_yaml(DOMAIN_PATH, self.domain)
    
    def fix_missing_slots(self):
        """Add missing slots to domain.yml."""
        # Extract slot references from custom actions
        slot_references = set()
        if os.path.exists(ACTIONS_PATH):
            try:
                with open(ACTIONS_PATH, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Find slots accessed via tracker.get_slot
                    slot_pattern = r'tracker\.get_slot\([\'"](.+?)[\'"]\)'
                    slot_references.update(re.findall(slot_pattern, content))
                    
                    # Find slots set via SlotSet
                    slot_set_pattern = r'SlotSet\([\'"](.+?)[\'"]\)'
                    slot_references.update(re.findall(slot_set_pattern, content))
            except Exception as e:
                logger.error(f"Error checking slot references: {e}")
        
        # Get slots from domain
        domain_slots = set()
        if 'slots' in self.domain:
            for slot_name, slot_config in self.domain['slots'].items():
                if isinstance(slot_config, dict) and 'name' in slot_config:
                    domain_slots.add(slot_config['name'])
        
        # Add missing slots to domain
        slots_to_add = slot_references - domain_slots
        if slots_to_add:
            if 'slots' not in self.domain:
                self.domain['slots'] = {}
            
            for slot in slots_to_add:
                # Create default text slot
                self.domain['slots'][slot] = {
                    'type': 'text',
                    'influence_conversation': False
                }
                self.fixes.append(f"Added missing slot '{slot}' to domain.yml")
            
            self._save_yaml(DOMAIN_PATH, self.domain)
    
    def fix_regex_configuration(self):
        """Add RegexEntityExtractor to pipeline if needed."""
        # Check if there are regex patterns in NLU
        has_regex_patterns = False
        if self.nlu and 'nlu' in self.nlu:
            for item in self.nlu['nlu']:
                if item.get('regex') or (isinstance(item.get('examples', ''), str) and '[' in item.get('examples', '') and '](' in item.get('examples', '')):
                    has_regex_patterns = True
                    break
        
        if not has_regex_patterns:
            return
        
        # Check if RegexEntityExtractor is in pipeline
        has_regex_extractor = False
        if self.config and 'pipeline' in self.config:
            for component in self.config['pipeline']:
                if isinstance(component, dict) and component.get('name') == 'RegexEntityExtractor':
                    has_regex_extractor = True
                    break
        
        # Add RegexEntityExtractor if needed
        if has_regex_patterns and not has_regex_extractor:
            # Make sure pipeline exists
            if 'pipeline' not in self.config:
                self.config['pipeline'] = []
            
            # Find DIETClassifier or position to insert RegexEntityExtractor
            diet_position = -1
            for i, component in enumerate(self.config['pipeline']):
                if isinstance(component, dict) and component.get('name') == 'DIETClassifier':
                    diet_position = i
                    break
            
            # Add RegexEntityExtractor at appropriate position
            if diet_position >= 0:
                self.config['pipeline'].insert(diet_position, {'name': 'RegexEntityExtractor'})
            else:
                self.config['pipeline'].append({'name': 'RegexEntityExtractor'})
            
            self.fixes.append("Added RegexEntityExtractor to pipeline in config.yml")
            self._save_yaml(CONFIG_PATH, self.config)
    
    def fix_all(self):
        """Run all fixes."""
        logger.info("Running Rasa conflict fixes...")
        
        self.fix_missing_intents()
        self.fix_undefined_actions()
        self.fix_missing_entities()
        self.fix_missing_slots()
        self.fix_regex_configuration()
        
        if self.fixes:
            logger.info(f"Applied {len(self.fixes)} fixes:")
            for i, fix in enumerate(self.fixes, 1):
                logger.info(f"{i}. {fix}")
        else:
            logger.info("No fixes were needed!")
        
        return self.fixes

def main():
    """Main function to run conflict fixer."""
    try:
        print("Running Rasa conflict fixer...")
        print("This will automatically fix common issues in your Rasa configuration.")
        print("Backups will be created before making any changes.")
        
        fixer = ConflictFixer()
        fixes = fixer.fix_all()
        
        if fixes:
            print(f"\nApplied {len(fixes)} fixes:")
            for i, fix in enumerate(fixes, 1):
                print(f"{i}. {fix}")
            print("\nRecommendation: Now run 'python -m rasa train' to verify the fixes")
            return True
        else:
            print("\nNo fixes were needed!")
            return True
            
    except Exception as e:
        logger.error(f"Error during fix operation: {e}")
        print(f"Error during fix operation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 