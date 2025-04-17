#!/usr/bin/env python3
"""
Rasa Conflict Checker
--------------------
Analyzes Rasa configuration files to identify common training conflicts and inconsistencies.
"""

import os
import sys
import yaml
import re
import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rasa_conflicts.log')
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

class ConflictChecker:
    """Class to check for conflicts in Rasa files."""
    
    def __init__(self):
        self.domain = self._load_yaml(DOMAIN_PATH)
        self.nlu = self._load_yaml(NLU_PATH)
        self.stories = self._load_yaml(STORIES_PATH)
        self.rules = self._load_yaml(RULES_PATH)
        self.config = self._load_yaml(CONFIG_PATH)
        
        # Extract key components
        self.domain_intents = set(self.domain.get('intents', []))
        self.domain_actions = set(self.domain.get('actions', []))
        self.domain_responses = set(self.domain.get('responses', {}).keys())
        self.domain_entities = set(self.domain.get('entities', []))
        self.domain_slots = set(slot['name'] for slot in self.domain.get('slots', {}).values())
        
        self.nlu_intents = set()
        if self.nlu and 'nlu' in self.nlu:
            for item in self.nlu['nlu']:
                if 'intent' in item:
                    self.nlu_intents.add(item['intent'])
        
        self.story_actions = set()
        self.story_intents = set()
        self._extract_story_components()
        
        self.custom_actions = self._extract_custom_actions()
        
        # Issues tracking
        self.issues = []
        
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
    
    def _extract_story_components(self):
        """Extract intents and actions from stories and rules."""
        # Process stories
        if self.stories and 'stories' in self.stories:
            for story in self.stories['stories']:
                if 'steps' in story:
                    for step in story['steps']:
                        if 'intent' in step:
                            self.story_intents.add(step['intent'])
                        if 'action' in step:
                            self.story_actions.add(step['action'])
        
        # Process rules
        if self.rules and 'rules' in self.rules:
            for rule in self.rules['rules']:
                if 'steps' in rule:
                    for step in rule['steps']:
                        if 'intent' in step:
                            self.story_intents.add(step['intent'])
                        if 'action' in step:
                            self.story_actions.add(step['action'])
    
    def _extract_custom_actions(self) -> Set[str]:
        """Extract custom action names from actions.py file."""
        custom_actions = set()
        
        if not os.path.exists(ACTIONS_PATH):
            return custom_actions
        
        try:
            with open(ACTIONS_PATH, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Find all class definitions that inherit from Action
                class_pattern = r'class\s+(\w+)\s*\(.*?Action\)'
                class_matches = re.findall(class_pattern, content)
                
                # Extract name method return values
                for class_name in class_matches:
                    name_pattern = rf'class\s+{class_name}.*?def\s+name.*?return\s+[\'"](.+?)[\'"]'
                    name_matches = re.findall(name_pattern, content, re.DOTALL)
                    if name_matches:
                        custom_actions.add(name_matches[0])
        except Exception as e:
            logger.error(f"Error extracting custom actions: {e}")
        
        return custom_actions
    
    def check_intent_consistency(self):
        """Check if intents are consistently defined across files."""
        # Check intents in domain vs NLU
        domain_only_intents = self.domain_intents - self.nlu_intents
        nlu_only_intents = self.nlu_intents - self.domain_intents
        
        if domain_only_intents:
            self.issues.append(f"Intents defined in domain.yml but missing in NLU data: {domain_only_intents}")
        
        if nlu_only_intents:
            self.issues.append(f"Intents defined in NLU data but missing in domain.yml: {nlu_only_intents}")
        
        # Check intents used in stories but not defined
        story_undefined_intents = self.story_intents - self.domain_intents
        if story_undefined_intents:
            self.issues.append(f"Intents used in stories/rules but not defined in domain.yml: {story_undefined_intents}")
    
    def check_action_consistency(self):
        """Check if actions are consistently defined and used."""
        # All possible actions (custom + responses + default)
        all_defined_actions = self.custom_actions | self.domain_actions | self.domain_responses
        
        # Add default actions (utter_*)
        for response in self.domain_responses:
            if response.startswith('utter_'):
                all_defined_actions.add(response)
        
        # Check for actions used in stories but not defined
        undefined_actions = self.story_actions - all_defined_actions
        # Filter out default Rasa actions like 'action_listen'
        undefined_actions = {action for action in undefined_actions 
                           if not action.startswith('action_') or action not in ['action_listen', 'action_restart', 'action_default_fallback', 'action_session_start']}
        
        if undefined_actions:
            self.issues.append(f"Actions used in stories/rules but not defined: {undefined_actions}")
        
        # Check for custom actions that might have naming conflicts
        action_prefixes = defaultdict(list)
        for action in self.custom_actions:
            prefix = action.split('_')[0] if '_' in action else action
            action_prefixes[prefix].append(action)
        
        for prefix, actions in action_prefixes.items():
            if len(actions) > 1:
                self.issues.append(f"Potential action name conflict with prefix '{prefix}': {actions}")
    
    def check_entity_consistency(self):
        """Check if entities are consistently defined."""
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
        
        # Compare with domain entities
        nlu_only_entities = nlu_entities - self.domain_entities
        if nlu_only_entities:
            self.issues.append(f"Entities used in NLU examples but not defined in domain.yml: {nlu_only_entities}")
    
    def check_slot_consistency(self):
        """Check if slots are consistently defined and used."""
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
                logger.error(f"Error checking slot consistency: {e}")
        
        # Compare with domain slots
        undefined_slots = slot_references - self.domain_slots
        if undefined_slots:
            self.issues.append(f"Slots referenced in actions but not defined in domain.yml: {undefined_slots}")
    
    def check_story_conflicts(self):
        """Check for potential conflicts in stories."""
        # Extract story paths to identify potential conflicts
        story_paths = defaultdict(list)
        
        if self.stories and 'stories' in self.stories:
            for i, story in enumerate(self.stories['stories']):
                if 'steps' in story:
                    path = []
                    for step in story['steps']:
                        if 'intent' in step:
                            path.append(f"intent:{step['intent']}")
                        elif 'action' in step:
                            path.append(f"action:{step['action']}")
                    
                    if path:
                        path_key = tuple(path[:2])  # Use first two steps as key
                        story_paths[path_key].append(f"Story #{i+1}: {story.get('story', f'Unnamed Story {i+1}')}")
        
        # Check for story paths with the same start but different continuations
        for path_key, stories in story_paths.items():
            if len(stories) > 1:
                self.issues.append(f"Potential story conflict with same start sequence {path_key}: {stories}")
    
    def check_regex_entity_extraction(self):
        """Check for potential issues with regex entity extraction."""
        # Check for proper configuration of regex entity extraction
        has_regex_entity_extractor = False
        if self.config and 'pipeline' in self.config:
            for component in self.config['pipeline']:
                if isinstance(component, dict) and component.get('name') == 'RegexEntityExtractor':
                    has_regex_entity_extractor = True
                    break
        
        # Look for regex patterns in NLU data
        has_regex_patterns = False
        if self.nlu and 'nlu' in self.nlu:
            for item in self.nlu['nlu']:
                if item.get('regex') or (isinstance(item.get('examples', ''), str) and '[' in item.get('examples', '') and '](' in item.get('examples', '')):
                    has_regex_patterns = True
                    break
        
        if has_regex_patterns and not has_regex_entity_extractor:
            self.issues.append("Regex patterns found in NLU data, but RegexEntityExtractor is not configured in the pipeline")
    
    def check_training_data_balance(self):
        """Check for potential imbalances in training data."""
        intent_examples = defaultdict(int)
        
        if self.nlu and 'nlu' in self.nlu:
            for item in self.nlu['nlu']:
                if 'intent' in item and 'examples' in item:
                    examples = item['examples']
                    if isinstance(examples, str):
                        # Count non-empty lines
                        count = len([line for line in examples.split('\n') if line.strip() and line.strip().startswith('-')])
                        intent_examples[item['intent']] = count
        
        # Check for intents with very few examples
        for intent, count in intent_examples.items():
            if count < 3:
                self.issues.append(f"Intent '{intent}' has only {count} examples, which may not be enough for good NLU performance")
        
        # Check for large imbalances
        if intent_examples:
            avg_examples = sum(intent_examples.values()) / len(intent_examples)
            for intent, count in intent_examples.items():
                if count > avg_examples * 3:
                    self.issues.append(f"Intent '{intent}' has {count} examples, which is significantly more than the average ({avg_examples:.1f}) and may cause training imbalance")
    
    def run_all_checks(self):
        """Run all conflict checks."""
        logger.info("Running Rasa conflict checks...")
        
        self.check_intent_consistency()
        self.check_action_consistency()
        self.check_entity_consistency()
        self.check_slot_consistency()
        self.check_story_conflicts()
        self.check_regex_entity_extraction()
        self.check_training_data_balance()
        
        if self.issues:
            logger.info(f"Found {len(self.issues)} potential issues:")
            for i, issue in enumerate(self.issues, 1):
                logger.info(f"{i}. {issue}")
        else:
            logger.info("No issues found in Rasa configuration!")
        
        return self.issues

def main():
    """Main function to run conflict checker."""
    try:
        checker = ConflictChecker()
        issues = checker.run_all_checks()
        
        if issues:
            print(f"\nFound {len(issues)} potential issues:")
            for i, issue in enumerate(issues, 1):
                print(f"{i}. {issue}")
            print("\nRecommendation: Fix these issues and then run the reset_rasa.py script")
            return False
        else:
            print("\nNo issues found in your Rasa configuration!")
            return True
            
    except Exception as e:
        logger.error(f"Error during conflict check: {e}")
        print(f"Error during conflict check: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 