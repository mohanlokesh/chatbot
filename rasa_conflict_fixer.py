#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import yaml
from colorama import Fore, Style, init

# Initialize colorama
init()

def print_error(message):
    print(f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}")

def print_warning(message):
    print(f"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")

def print_info(message):
    print(f"{Fore.BLUE}INFO: {message}{Style.RESET_ALL}")

def print_success(message):
    print(f"{Fore.GREEN}SUCCESS: {message}{Style.RESET_ALL}")

def load_yaml_file(file_path):
    """Load a YAML file and return its contents"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_error(f"Error loading {file_path}: {str(e)}")
        return None

def save_yaml_file(file_path, data):
    """Save a YAML file with proper formatting"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception as e:
        print_error(f"Error saving {file_path}: {str(e)}")
        return False

def find_domain_yml(directory):
    """Find domain.yml file in the directory"""
    domain_path = os.path.join(directory, "domain.yml")
    if os.path.exists(domain_path):
        return domain_path
    return None

def find_config_yml(directory):
    """Find config.yml file in the directory"""
    config_path = os.path.join(directory, "config.yml")
    if os.path.exists(config_path):
        return config_path
    return None

def find_data_files(directory):
    """Find data files in the directory"""
    data_dir = os.path.join(directory, "data")
    
    nlu_file = os.path.join(data_dir, "nlu.yml")
    if not os.path.exists(nlu_file):
        nlu_file = None
    
    stories_file = os.path.join(data_dir, "stories.yml")
    if not os.path.exists(stories_file):
        stories_file = os.path.join(directory, "stories.yml")
        if not os.path.exists(stories_file):
            stories_file = None
    
    rules_file = os.path.join(data_dir, "rules.yml")
    if not os.path.exists(rules_file):
        rules_file = os.path.join(directory, "rules.yml")
        if not os.path.exists(rules_file):
            rules_file = None
    
    return {
        "nlu": nlu_file,
        "stories": stories_file,
        "rules": rules_file
    }

def extract_intents_from_nlu(nlu_data):
    """Extract intents from NLU data"""
    intents = []
    
    if not nlu_data or "nlu" not in nlu_data:
        return intents
    
    for item in nlu_data.get("nlu", []):
        if isinstance(item, dict) and "intent" in item:
            intents.append(item["intent"])
    
    return intents

def extract_actions_from_stories(stories_data):
    """Extract actions from stories data"""
    actions = set()
    
    if not stories_data or "stories" not in stories_data:
        return actions
    
    for story in stories_data.get("stories", []):
        if "steps" in story:
            for step in story["steps"]:
                if "action" in step:
                    actions.add(step["action"])
    
    return actions

def extract_intents_from_stories(stories_data):
    """Extract intents from stories data"""
    intents = set()
    
    if not stories_data or "stories" not in stories_data:
        return intents
    
    for story in stories_data.get("stories", []):
        if "steps" in story:
            for step in story["steps"]:
                if "intent" in step:
                    intents.add(step["intent"])
    
    return intents

def extract_intents_from_rules(rules_data):
    """Extract intents from rules data"""
    intents = set()
    
    if not rules_data or "rules" not in rules_data:
        return intents
    
    for rule in rules_data.get("rules", []):
        if "steps" in rule:
            for step in rule["steps"]:
                if "intent" in step:
                    intents.add(step["intent"])
    
    return intents

def fix_missing_intents(domain_file, domain_data, story_intents, rule_intents):
    """Fix missing intents in domain.yml"""
    if not domain_data:
        print_error("Domain data is empty or cannot be loaded")
        return False
    
    if "intents" not in domain_data:
        domain_data["intents"] = []
    
    intents_fixed = False
    domain_intents = domain_data["intents"]
    
    # Add missing intents from stories
    for intent in story_intents:
        if intent not in domain_intents:
            print_info(f"Adding missing intent '{intent}' to domain.yml")
            domain_intents.append(intent)
            intents_fixed = True
    
    # Add missing intents from rules
    for intent in rule_intents:
        if intent not in domain_intents:
            print_info(f"Adding missing intent '{intent}' to domain.yml")
            domain_intents.append(intent)
            intents_fixed = True
    
    if intents_fixed:
        print_success("Fixed missing intents in domain.yml")
        return save_yaml_file(domain_file, domain_data)
    
    return True

def fix_undefined_intents(stories_file, stories_data, rules_file, rules_data, domain_data):
    """Fix undefined intents in stories and rules"""
    if not domain_data or "intents" not in domain_data:
        print_error("Domain data is missing or intents section not found")
        return False
    
    domain_intents = domain_data["intents"]
    fixes_applied = False
    
    # Fix undefined intents in stories
    if stories_data and "stories" in stories_data:
        stories_fixed = False
        
        for story in stories_data["stories"]:
            if "steps" in story:
                for i, step in enumerate(story["steps"]):
                    if "intent" in step and step["intent"] not in domain_intents:
                        # Get a suitable replacement from domain intents
                        if len(domain_intents) > 0:
                            # Try to find a similar intent
                            suitable_intent = find_similar_intent(step["intent"], domain_intents)
                            print_info(f"Replacing undefined intent '{step['intent']}' with '{suitable_intent}' in stories")
                            story["steps"][i]["intent"] = suitable_intent
                            stories_fixed = True
        
        if stories_fixed:
            print_success("Fixed undefined intents in stories.yml")
            if not save_yaml_file(stories_file, stories_data):
                return False
            fixes_applied = True
    
    # Fix undefined intents in rules
    if rules_data and "rules" in rules_data:
        rules_fixed = False
        
        for rule in rules_data["rules"]:
            if "steps" in rule:
                for i, step in enumerate(rule["steps"]):
                    if "intent" in step and step["intent"] not in domain_intents:
                        # Get a suitable replacement from domain intents
                        if len(domain_intents) > 0:
                            # Try to find a similar intent
                            suitable_intent = find_similar_intent(step["intent"], domain_intents)
                            print_info(f"Replacing undefined intent '{step['intent']}' with '{suitable_intent}' in rules")
                            rule["steps"][i]["intent"] = suitable_intent
                            rules_fixed = True
        
        if rules_fixed:
            print_success("Fixed undefined intents in rules.yml")
            if not save_yaml_file(rules_file, rules_data):
                return False
            fixes_applied = True
    
    return True

def find_similar_intent(undefined_intent, domain_intents):
    """Find a similar intent in domain intents"""
    # Simple implementation - can be improved with string similarity algorithms
    
    # Check if the undefined intent is a more specific version of a domain intent
    for intent in domain_intents:
        if undefined_intent.startswith(intent) or intent.startswith(undefined_intent):
            return intent
    
    # Default to the first intent if no similarity found
    return domain_intents[0]

def fix_missing_actions(domain_file, domain_data, story_actions):
    """Fix missing actions in domain.yml"""
    if not domain_data:
        print_error("Domain data is empty or cannot be loaded")
        return False
    
    if "actions" not in domain_data:
        domain_data["actions"] = []
    
    actions_fixed = False
    domain_actions = domain_data["actions"]
    domain_responses = domain_data.get("responses", {}).keys()
    
    # Add missing actions to domain
    for action in story_actions:
        if (action not in domain_actions and 
            action not in domain_responses and 
            not action.startswith("action_default_")):
            print_info(f"Adding missing action '{action}' to domain.yml")
            domain_actions.append(action)
            actions_fixed = True
    
    if actions_fixed:
        print_success("Fixed missing actions in domain.yml")
        return save_yaml_file(domain_file, domain_data)
    
    return True

def fix_undefined_actions(stories_file, stories_data, domain_data):
    """Fix undefined actions in stories"""
    if not domain_data:
        print_error("Domain data is empty or cannot be loaded")
        return False
    
    domain_actions = domain_data.get("actions", [])
    domain_responses = domain_data.get("responses", {}).keys()
    
    # Prepare the list of all valid actions
    valid_actions = list(domain_actions)
    valid_actions.extend([f"utter_{resp[6:]}" for resp in domain_responses if resp.startswith("utter_")])
    
    # Fix undefined actions in stories
    if stories_data and "stories" in stories_data:
        stories_fixed = False
        
        for story in stories_data["stories"]:
            if "steps" in story:
                for i, step in enumerate(story["steps"]):
                    if "action" in step and step["action"] not in valid_actions:
                        # Get a suitable replacement action
                        suitable_action = find_similar_action(step["action"], valid_actions)
                        print_info(f"Replacing undefined action '{step['action']}' with '{suitable_action}' in stories")
                        story["steps"][i]["action"] = suitable_action
                        stories_fixed = True
        
        if stories_fixed:
            print_success("Fixed undefined actions in stories.yml")
            return save_yaml_file(stories_file, stories_data)
    
    return True

def find_similar_action(undefined_action, valid_actions):
    """Find a similar action in valid actions"""
    # Simple implementation - can be improved with string similarity algorithms
    
    # Check if action starts with utter_
    if undefined_action.startswith("utter_"):
        for action in valid_actions:
            if action.startswith("utter_") and (undefined_action[6:] in action[6:] or action[6:] in undefined_action[6:]):
                return action
    
    # Check if action starts with action_
    if undefined_action.startswith("action_"):
        for action in valid_actions:
            if action.startswith("action_") and (undefined_action[7:] in action[7:] or action[7:] in undefined_action[7:]):
                return action
    
    # Default to a standard action if no similarity found
    for action in valid_actions:
        if action.startswith("utter_"):
            return action
    
    # Fallback to first valid action
    return valid_actions[0] if valid_actions else "action_default_fallback"

def fix_missing_extractors(config_file, config_data):
    """Fix missing extractors in config.yml"""
    if not config_data:
        print_error("Config data is empty or cannot be loaded")
        return False
    
    if "pipeline" not in config_data:
        print_error("Pipeline section not found in config.yml")
        return False
    
    pipeline = config_data["pipeline"]
    pipeline_names = [item.get("name") if isinstance(item, dict) else item for item in pipeline]
    
    extractors_fixed = False
    
    # Add EntitySynonymMapper if missing
    if "EntitySynonymMapper" not in pipeline_names:
        print_info("Adding missing 'EntitySynonymMapper' to config.yml pipeline")
        
        # Find a good position to insert - after DIETClassifier if present
        diet_pos = -1
        for i, item in enumerate(pipeline):
            if isinstance(item, dict) and item.get("name") == "DIETClassifier":
                diet_pos = i
                break
        
        # Insert after DIETClassifier or at the end if not found
        if diet_pos >= 0:
            pipeline.insert(diet_pos + 1, {"name": "EntitySynonymMapper"})
        else:
            pipeline.append({"name": "EntitySynonymMapper"})
        
        extractors_fixed = True
    
    if extractors_fixed:
        print_success("Fixed missing extractors in config.yml")
        return save_yaml_file(config_file, config_data)
    
    return True

def run_conflict_fixer(directory):
    """Run conflict fixing on Rasa project files"""
    print_info(f"Fixing conflicts in Rasa project: {directory}")
    
    # Find project files
    domain_file = find_domain_yml(directory)
    config_file = find_config_yml(directory)
    data_files = find_data_files(directory)
    
    if not domain_file:
        print_error("domain.yml file not found")
        return False
    
    if not config_file:
        print_error("config.yml file not found")
        return False
    
    # Load files
    domain_data = load_yaml_file(domain_file)
    config_data = load_yaml_file(config_file)
    
    nlu_data = None
    if data_files["nlu"]:
        nlu_data = load_yaml_file(data_files["nlu"])
    
    stories_data = None
    if data_files["stories"]:
        stories_data = load_yaml_file(data_files["stories"])
    
    rules_data = None
    if data_files["rules"]:
        rules_data = load_yaml_file(data_files["rules"])
    
    # Extract data
    nlu_intents = extract_intents_from_nlu(nlu_data) if nlu_data else []
    story_intents = extract_intents_from_stories(stories_data) if stories_data else set()
    rule_intents = extract_intents_from_rules(rules_data) if rules_data else set()
    story_actions = extract_actions_from_stories(stories_data) if stories_data else set()
    
    # Fix issues
    fixes_successful = True
    
    # Fix missing intents in domain.yml
    if not fix_missing_intents(domain_file, domain_data, story_intents, rule_intents):
        fixes_successful = False
    
    # Reload domain data after fixes
    domain_data = load_yaml_file(domain_file)
    
    # Fix undefined intents in stories.yml and rules.yml
    if data_files["stories"] and data_files["rules"]:
        if not fix_undefined_intents(data_files["stories"], stories_data, data_files["rules"], rules_data, domain_data):
            fixes_successful = False
    
    # Fix missing actions in domain.yml
    if not fix_missing_actions(domain_file, domain_data, story_actions):
        fixes_successful = False
    
    # Reload domain data after fixes
    domain_data = load_yaml_file(domain_file)
    
    # Fix undefined actions in stories.yml
    if data_files["stories"]:
        if not fix_undefined_actions(data_files["stories"], stories_data, domain_data):
            fixes_successful = False
    
    # Fix missing extractors in config.yml
    if not fix_missing_extractors(config_file, config_data):
        fixes_successful = False
    
    if fixes_successful:
        print_success("All conflicts fixed successfully")
    else:
        print_warning("Some conflicts could not be fixed")
    
    return fixes_successful

def main():
    parser = argparse.ArgumentParser(description="Fix conflicts in Rasa project files")
    parser.add_argument("--directory", default=".", help="Directory of the Rasa project (default: current directory)")
    
    args = parser.parse_args()
    
    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        print_error(f"Directory does not exist: {directory}")
        return 1
    
    fixes_successful = run_conflict_fixer(directory)
    
    return 0 if fixes_successful else 1

if __name__ == "__main__":
    sys.exit(main()) 