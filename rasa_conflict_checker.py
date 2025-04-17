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

def check_missing_intents(domain_data, nlu_intents, story_intents, rule_intents):
    """Check for missing intents in domain.yml"""
    issues = []
    
    if not domain_data or "intents" not in domain_data:
        issues.append("Domain file is missing the 'intents' section")
        return issues
    
    domain_intents = domain_data["intents"]
    
    # Check intents used in stories but not in domain
    for intent in story_intents:
        if intent not in domain_intents:
            issues.append(f"Intent '{intent}' is used in stories but not defined in domain.yml")
    
    # Check intents used in rules but not in domain
    for intent in rule_intents:
        if intent not in domain_intents:
            issues.append(f"Intent '{intent}' is used in rules but not defined in domain.yml")
    
    return issues

def check_undefined_intents(domain_data, story_intents, rule_intents):
    """Check for undefined intents in stories and rules"""
    issues = []
    
    if not domain_data or "intents" not in domain_data:
        return issues
    
    domain_intents = domain_data["intents"]
    
    # Check if story intents are defined in domain
    for intent in story_intents:
        if intent not in domain_intents:
            issues.append(f"Story intent '{intent}' is not defined in domain.yml")
    
    # Check if rule intents are defined in domain
    for intent in rule_intents:
        if intent not in domain_intents:
            issues.append(f"Rule intent '{intent}' is not defined in domain.yml")
    
    return issues

def check_missing_actions(domain_data, story_actions):
    """Check for missing actions in domain.yml"""
    issues = []
    
    if not domain_data:
        issues.append("Domain file is empty or could not be loaded")
        return issues
    
    domain_actions = domain_data.get("actions", [])
    
    # Check for missing utter responses
    domain_responses = domain_data.get("responses", {}).keys()
    
    # Check actions used in stories but not in domain
    for action in story_actions:
        if (action not in domain_actions and 
            action not in domain_responses and 
            not action.startswith("action_") and 
            not action.startswith("utter_")):
            issues.append(f"Action '{action}' is used in stories but not defined in domain.yml")
    
    return issues

def check_undefined_actions(domain_data, story_actions):
    """Check for undefined actions in stories"""
    issues = []
    
    if not domain_data:
        return issues
    
    domain_actions = domain_data.get("actions", [])
    domain_responses = domain_data.get("responses", {}).keys()
    
    # Check if story actions are defined
    for action in story_actions:
        if (action not in domain_actions and 
            action not in domain_responses and 
            not action.startswith("action_default_")):
            issues.append(f"Story action '{action}' is not defined in domain.yml or as a response")
    
    return issues

def check_missing_extractors(config_data):
    """Check for missing extractors in config.yml"""
    issues = []
    
    if not config_data or "pipeline" not in config_data:
        issues.append("Config file is missing the 'pipeline' section")
        return issues
    
    pipeline = config_data["pipeline"]
    pipeline_names = [item.get("name") if isinstance(item, dict) else item for item in pipeline]
    
    # Check if EntitySynonymMapper is in the pipeline
    if "EntitySynonymMapper" not in pipeline_names:
        issues.append("Missing 'EntitySynonymMapper' extractor in config.yml pipeline")
    
    return issues

def run_conflict_check(directory):
    """Run conflict checking on Rasa project files"""
    print_info(f"Checking for conflicts in Rasa project: {directory}")
    issues_found = False
    
    # Find project files
    domain_file = find_domain_yml(directory)
    config_file = find_config_yml(directory)
    data_files = find_data_files(directory)
    
    if not domain_file:
        print_error("domain.yml file not found")
        return True
    
    if not config_file:
        print_error("config.yml file not found")
        return True
    
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
    
    # Run checks
    issues = []
    
    # Check for missing and undefined intents
    issues.extend(check_missing_intents(domain_data, nlu_intents, story_intents, rule_intents))
    issues.extend(check_undefined_intents(domain_data, story_intents, rule_intents))
    
    # Check for missing and undefined actions
    issues.extend(check_missing_actions(domain_data, story_actions))
    issues.extend(check_undefined_actions(domain_data, story_actions))
    
    # Check for missing extractors
    issues.extend(check_missing_extractors(config_data))
    
    # Print issues
    if issues:
        print_error(f"Found {len(issues)} conflicts:")
        for issue in issues:
            print(f"  - {issue}")
        issues_found = True
    else:
        print_success("No issues found")
    
    return issues_found

def main():
    parser = argparse.ArgumentParser(description="Check for conflicts in Rasa project files")
    parser.add_argument("--directory", default=".", help="Directory of the Rasa project (default: current directory)")
    
    args = parser.parse_args()
    
    directory = os.path.abspath(args.directory)
    if not os.path.isdir(directory):
        print_error(f"Directory does not exist: {directory}")
        return 1
    
    issues_found = run_conflict_check(directory)
    
    return 1 if issues_found else 0

if __name__ == "__main__":
    sys.exit(main()) 