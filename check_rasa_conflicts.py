#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import yaml
import logging
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import collections

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rasa_conflicts.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RasaConflictChecker")

# Configuration paths
RASA_DIR = "."
DATA_DIR = os.path.join(RASA_DIR, "data")
DOMAIN_PATH = os.path.join(RASA_DIR, "domain.yml")
NLU_PATH = os.path.join(DATA_DIR, "nlu.yml")
STORIES_PATH = os.path.join(DATA_DIR, "stories.yml")
RULES_PATH = os.path.join(DATA_DIR, "rules.yml")
ACTIONS_PATH = os.path.join(RASA_DIR, "actions.py")
CONFIG_PATH = os.path.join(RASA_DIR, "config.yml")


class ConflictChecker:
    """
    A utility to check for configuration conflicts and inconsistencies in Rasa projects.
    """
    
    def __init__(self):
        self.domain_data = {}
        self.nlu_data = {}
        self.stories_data = {}
        self.rules_data = {}
        self.config_data = {}
        self.issue_count = 0
        self.warnings = 0
        self.details = []
        
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
            self.issue_count += 1
            self.details.append(f"ERROR: Could not load {file_path}. {str(e)}")
            return {}
    
    def _load_all_files(self) -> None:
        """Load all required Rasa configuration files."""
        self.domain_data = self._load_yaml(DOMAIN_PATH)
        self.nlu_data = self._load_yaml(NLU_PATH)
        self.stories_data = self._load_yaml(STORIES_PATH)
        self.rules_data = self._load_yaml(RULES_PATH)
        self.config_data = self._load_yaml(CONFIG_PATH)
    
    def check_missing_intents(self) -> int:
        """
        Check for intents that are defined in NLU but missing in domain, or vice versa.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
        # Extract intents from domain
        domain_intents = set(self.domain_data.get('intents', []))
        if not domain_intents:
            logger.warning("No intents defined in domain.yml")
        
        # Extract intents from NLU
        nlu_intents = set()
        for example in self.nlu_data.get('nlu', []):
            if example.get('intent'):
                nlu_intents.add(example.get('intent'))
        
        # Check for intents in NLU but not in domain
        missing_in_domain = nlu_intents - domain_intents
        if missing_in_domain:
            issues_count += len(missing_in_domain)
            logger.warning(f"Intents found in NLU but missing in domain: {', '.join(missing_in_domain)}")
            self.details.append(f"ISSUE: Intents in NLU but missing in domain: {', '.join(missing_in_domain)}")
        
        # Check for intents in domain but not in NLU
        missing_in_nlu = domain_intents - nlu_intents
        if missing_in_nlu:
            issues_count += len(missing_in_nlu)
            logger.warning(f"Intents found in domain but missing in NLU: {', '.join(missing_in_nlu)}")
            self.details.append(f"ISSUE: Intents in domain but missing in NLU: {', '.join(missing_in_nlu)}")
        
        return issues_count
    
    def check_undefined_actions(self) -> int:
        """
        Check for actions that are used in stories/rules but not defined in domain
        or custom actions without implementation.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
        # Extract actions from domain
        domain_actions = set(self.domain_data.get('actions', []))
        
        # Extract actions from stories and rules
        story_actions = set()
        for story in self.stories_data.get('stories', []):
            for step in story.get('steps', []):
                if 'action' in step:
                    story_actions.add(step['action'])
        
        for rule in self.rules_data.get('rules', []):
            for step in rule.get('steps', []):
                if 'action' in step:
                    story_actions.add(step['action'])
        
        # Check for actions in stories/rules but not in domain
        missing_in_domain = story_actions - domain_actions
        missing_in_domain = {action for action in missing_in_domain if not action.startswith('utter_')}
        
        if missing_in_domain:
            issues_count += len(missing_in_domain)
            logger.warning(f"Actions used in stories/rules but missing in domain: {', '.join(missing_in_domain)}")
            self.details.append(f"ISSUE: Actions used in stories/rules but not defined: {', '.join(missing_in_domain)}")
        
        # Check for custom actions without implementation
        if os.path.exists(ACTIONS_PATH):
            with open(ACTIONS_PATH, 'r', encoding='utf-8') as f:
                actions_content = f.read()
            
            custom_actions = {action for action in domain_actions if action.startswith('action_') and not action == 'action_restart'}
            
            for action in custom_actions:
                class_name = 'class ' + ''.join(word.capitalize() for word in action.split('_')) + '('
                if class_name not in actions_content:
                    issues_count += 1
                    logger.warning(f"Custom action {action} is defined in domain but has no implementation in actions.py")
                    self.details.append(f"ISSUE: Custom action {action} is defined in domain but has no implementation in actions.py")
        
        return issues_count
    
    def check_missing_entities(self) -> int:
        """
        Check for entities that are used in NLU but not defined in domain.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
        # Extract entities from domain
        domain_entities = set(self.domain_data.get('entities', []))
        
        # Extract entities from NLU
        nlu_entities = set()
        for example in self.nlu_data.get('nlu', []):
            if 'examples' in example:
                entity_pattern = r'\[.*?\]\((\w+)\)'
                for match in re.finditer(entity_pattern, example['examples']):
                    nlu_entities.add(match.group(1))
        
        # Check for entities in NLU but not in domain
        missing_in_domain = nlu_entities - domain_entities
        if missing_in_domain:
            issues_count += len(missing_in_domain)
            logger.warning(f"Entities found in NLU but missing in domain: {', '.join(missing_in_domain)}")
            self.details.append(f"ISSUE: Entities used in NLU but missing in domain: {', '.join(missing_in_domain)}")
        
        return issues_count
    
    def check_missing_slots(self) -> int:
        """
        Check for slots that are mentioned in stories/rules but not defined in domain.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
        # Extract slots from domain
        domain_slots = set(self.domain_data.get('slots', {}).keys())
        
        # Extract slots from stories and rules
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
        
        # Check for slots in stories/rules but not in domain
        missing_in_domain = story_slots - domain_slots
        if missing_in_domain:
            issues_count += len(missing_in_domain)
            logger.warning(f"Slots used in stories/rules but missing in domain: {', '.join(missing_in_domain)}")
            self.details.append(f"ISSUE: Slots used in stories/rules but not defined in domain: {', '.join(missing_in_domain)}")
        
        return issues_count
    
    def check_regex_configuration(self) -> int:
        """
        Check if RegexEntityExtractor is configured properly when regex features are used.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
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
                issues_count += 1
                logger.warning("Regex features are used in NLU but RegexEntityExtractor is not in the pipeline")
                self.details.append("ISSUE: Regex features are used in NLU but RegexEntityExtractor is not configured in pipeline")
        
        return issues_count
    
    def check_story_conflicts(self) -> int:
        """
        Check for potential conflicts in stories.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
        # Extract stories with same starting conditions
        story_paths = {}
        
        for story in self.stories_data.get('stories', []):
            if story.get('steps') and len(story.get('steps')) >= 2:
                # Get the first intent and action (conversation start)
                first_steps = []
                for step in story.get('steps')[:2]:
                    if 'intent' in step:
                        first_steps.append(f"intent:{step['intent']}")
                    if 'action' in step:
                        first_steps.append(f"action:{step['action']}")
                
                if first_steps:
                    path_key = '->'.join(first_steps)
                    if path_key in story_paths:
                        story_paths[path_key].append(story.get('story'))
                    else:
                        story_paths[path_key] = [story.get('story')]
        
        # Report potential conflicts
        for path, stories in story_paths.items():
            if len(stories) > 1:
                issues_count += 1
                logger.warning(f"Potential story conflict: {len(stories)} stories start with the same path ({path}): {', '.join(stories)}")
                self.details.append(f"WARNING: Potential story conflict: {len(stories)} stories start with the same path ({path}): {', '.join(stories)}")
        
        return issues_count
    
    def check_training_data_imbalance(self) -> int:
        """
        Check for imbalanced training data in NLU.
        
        Returns:
            Number of issues found
        """
        issues_count = 0
        
        # Count examples per intent
        intent_examples = {}
        for example in self.nlu_data.get('nlu', []):
            if example.get('intent') and 'examples' in example:
                intent = example.get('intent')
                examples_text = example.get('examples')
                count = len(re.findall(r'- ', examples_text))
                intent_examples[intent] = count
        
        if intent_examples:
            # Calculate statistics
            intent_counts = list(intent_examples.values())
            avg_count = sum(intent_counts) / len(intent_counts)
            min_count = min(intent_counts)
            max_count = max(intent_counts)
            
            # Check for intents with few examples
            few_examples = []
            for intent, count in intent_examples.items():
                if count < 3:
                    few_examples.append(f"{intent} ({count})")
            
            if few_examples:
                issues_count += len(few_examples)
                logger.warning(f"Intents with too few examples (<3): {', '.join(few_examples)}")
                self.details.append(f"WARNING: Intents with too few examples: {', '.join(few_examples)}")
            
            # Check for high imbalance
            if max_count > 5 * min_count:
                issues_count += 1
                most_examples = max(intent_examples.items(), key=lambda x: x[1])
                least_examples = min(intent_examples.items(), key=lambda x: x[1])
                logger.warning(f"High intent imbalance: {most_examples[0]} has {most_examples[1]} examples " +
                              f"while {least_examples[0]} has only {least_examples[1]}")
                self.details.append(f"WARNING: High intent imbalance: {most_examples[0]} has {most_examples[1]} examples " +
                              f"while {least_examples[0]} has only {least_examples[1]}")
        
        return issues_count
    
    def run_all_checks(self) -> int:
        """
        Run all conflict checks and return the total number of issues found.
        
        Returns:
            Total number of issues found
        """
        logger.info("Starting Rasa conflict checks...")
        
        self.issue_count = 0
        self.warnings = 0
        self.details = []
        
        # Run all checks
        self.issue_count += self.check_missing_intents()
        self.issue_count += self.check_undefined_actions()
        self.issue_count += self.check_missing_entities()
        self.issue_count += self.check_missing_slots()
        self.issue_count += self.check_regex_configuration()
        self.issue_count += self.check_story_conflicts()
        self.issue_count += self.check_training_data_imbalance()
        
        # Run checks that produce warnings
        self.warnings += self.check_training_data_imbalance()
        
        logger.info(f"Completed Rasa conflict checks: found {self.issue_count} potential issues and {self.warnings} warnings")
        
        return self.issue_count

    def print_report(self):
        """Print a summary of found issues and warnings."""
        logger.info("=" * 80)
        logger.info("RASA CONFLICT CHECK REPORT")
        logger.info("=" * 80)
        
        if self.issue_count == 0 and self.warnings == 0:
            logger.info("No issues found! Your Rasa project looks good.")
            return
        
        if self.issue_count > 0:
            logger.info(f"Found {self.issue_count} issues that need to be fixed:")
            for detail in self.details:
                if detail.startswith("ISSUE:") or detail.startswith("ERROR:"):
                    logger.info(f"  - {detail}")
        
        if self.warnings > 0:
            logger.info(f"Found {self.warnings} warnings to consider:")
            for detail in self.details:
                if detail.startswith("WARNING:"):
                    logger.info(f"  - {detail}")
        
        logger.info("\nRECOMMENDED NEXT STEPS:")
        if self.issue_count > 0:
            logger.info("1. Run 'python fix_rasa_conflicts.py' to automatically fix detected issues")
            logger.info("2. After fixing, re-run this checker to verify all issues are resolved")
        else:
            logger.info("1. Address the warnings if they impact your bot's performance")
        
        logger.info("3. Train your model: python -m rasa train")
        logger.info("=" * 80)


def main():
    """Run the Rasa conflict checker."""
    try:
        checker = ConflictChecker()
        issue_count = checker.run_all_checks()
        checker.print_report()
        
        print(f"\nSummary: Found {issue_count} potential issues and {checker.warnings} warnings in your Rasa project.")
        
        if issue_count > 0 or checker.warnings > 0:
            print("\nTo automatically fix some of these issues, you can run:")
            print("python fix_rasa_conflicts.py")
        
        return issue_count
    except Exception as e:
        logger.error(f"Error during conflict checking: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 