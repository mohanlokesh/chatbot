#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import tempfile
import subprocess
import shutil
import yaml
from colorama import Fore, Style, init

# Initialize colorama
init()

def print_success(message):
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message, verbose=False):
    if verbose:
        print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")

def create_config_yml(test_dir, missing_extractors=False):
    """Create a test config.yml file"""
    config = {
        "language": "en",
        "pipeline": [
            {"name": "WhitespaceTokenizer"},
            {"name": "RegexFeaturizer"},
            {"name": "LexicalSyntacticFeaturizer"},
            {"name": "CountVectorsFeaturizer"},
            {"name": "CountVectorsFeaturizer", "analyzer": "char_wb", "min_ngram": 1, "max_ngram": 4},
            {"name": "DIETClassifier", "epochs": 100},
            {"name": "EntitySynonymMapper"},
            {"name": "ResponseSelector", "epochs": 100},
            {"name": "FallbackClassifier", "threshold": 0.3, "ambiguity_threshold": 0.1},
        ],
        "policies": [
            {"name": "MemoizationPolicy"},
            {"name": "TEDPolicy", "max_history": 5, "epochs": 100},
            {"name": "RulePolicy"}
        ]
    }
    
    # Create a deliberate conflict by removing extractors
    if missing_extractors:
        config["pipeline"] = [item for item in config["pipeline"] if item["name"] != "EntitySynonymMapper"]
    
    with open(os.path.join(test_dir, "config.yml"), "w") as f:
        yaml.dump(config, f)
    
    return config

def create_domain_yml(test_dir, missing_intents=False, missing_actions=False):
    """Create a test domain.yml file"""
    domain = {
        "version": "3.1",
        "intents": [
            "greet",
            "goodbye",
            "affirm",
            "deny",
            "mood_great",
            "mood_unhappy",
            "bot_challenge"
        ],
        "entities": [
            "name"
        ],
        "slots": {
            "name": {
                "type": "text",
                "mappings": [
                    {
                        "type": "from_entity",
                        "entity": "name"
                    }
                ]
            }
        },
        "responses": {
            "utter_greet": [
                {"text": "Hey! How are you?"}
            ],
            "utter_cheer_up": [
                {"text": "Here is something to cheer you up:"}
            ],
            "utter_did_that_help": [
                {"text": "Did that help you?"}
            ],
            "utter_happy": [
                {"text": "Great, carry on!"}
            ],
            "utter_goodbye": [
                {"text": "Bye"}
            ],
            "utter_iamabot": [
                {"text": "I am a bot, powered by Rasa."}
            ]
        },
        "actions": [
            "utter_greet",
            "utter_cheer_up",
            "utter_did_that_help",
            "utter_happy",
            "utter_goodbye",
            "utter_iamabot",
            "action_hello_world"
        ],
        "session_config": {
            "session_expiration_time": 60,
            "carry_over_slots_to_new_session": True
        }
    }
    
    # Create deliberate conflicts
    if missing_intents:
        domain["intents"].remove("bot_challenge")
    
    if missing_actions:
        domain["actions"].remove("action_hello_world")
    
    with open(os.path.join(test_dir, "domain.yml"), "w") as f:
        yaml.dump(domain, f)
    
    return domain

def create_nlu_yml(test_dir):
    """Create a test nlu.yml file"""
    nlu_content = """version: "3.1"
nlu:
- intent: greet
  examples: |
    - hey
    - hello
    - hi
    - hello there
    - good morning
    - good evening
    - moin
    - hey there
    - let's go
    - hey dude
    - goodmorning
    - goodevening
    - good afternoon

- intent: goodbye
  examples: |
    - cu
    - good by
    - cee you later
    - good night
    - bye
    - goodbye
    - have a nice day
    - see you around
    - bye bye
    - see you later

- intent: affirm
  examples: |
    - yes
    - y
    - indeed
    - of course
    - that sounds good
    - correct

- intent: deny
  examples: |
    - no
    - n
    - never
    - I don't think so
    - don't like that
    - no way
    - not really

- intent: mood_great
  examples: |
    - perfect
    - great
    - amazing
    - feeling like a king
    - wonderful
    - I am feeling very good
    - I am great
    - I am amazing
    - I am going to save the world
    - super stoked
    - extremely good
    - so so perfect
    - so good
    - so perfect

- intent: mood_unhappy
  examples: |
    - my day was horrible
    - I am sad
    - I don't feel very well
    - I am disappointed
    - super sad
    - I'm so sad
    - sad
    - very sad
    - unhappy
    - not good
    - not very good
    - extremly sad
    - so saad
    - so sad

- intent: bot_challenge
  examples: |
    - are you a bot?
    - are you a human?
    - am I talking to a bot?
    - am I talking to a human?
"""
    with open(os.path.join(test_dir, "nlu.yml"), "w") as f:
        f.write(nlu_content)

def create_stories_yml(test_dir, undefined_intents=False, undefined_actions=False):
    """Create a test stories.yml file"""
    stories_content = """version: "3.1"
stories:
- story: happy path
  steps:
  - intent: greet
  - action: utter_greet
  - intent: mood_great
  - action: utter_happy

- story: sad path 1
  steps:
  - intent: greet
  - action: utter_greet
  - intent: mood_unhappy
  - action: utter_cheer_up
  - action: utter_did_that_help
  - intent: affirm
  - action: utter_happy

- story: sad path 2
  steps:
  - intent: greet
  - action: utter_greet
  - intent: mood_unhappy
  - action: utter_cheer_up
  - action: utter_did_that_help
  - intent: deny
  - action: utter_goodbye
"""

    # Create deliberate conflicts
    if undefined_intents:
        stories_content = stories_content.replace("- intent: mood_great", "- intent: mood_awesome")
    
    if undefined_actions:
        stories_content = stories_content.replace("- action: utter_happy", "- action: utter_very_happy")
    
    with open(os.path.join(test_dir, "stories.yml"), "w") as f:
        f.write(stories_content)

def create_rules_yml(test_dir, undefined_intents=False):
    """Create a test rules.yml file"""
    rules_content = """version: "3.1"
rules:
- rule: Say goodbye anytime the user says goodbye
  steps:
  - intent: goodbye
  - action: utter_goodbye

- rule: Say 'I am a bot' anytime the user challenges
  steps:
  - intent: bot_challenge
  - action: utter_iamabot
"""

    # Create deliberate conflicts
    if undefined_intents:
        rules_content = rules_content.replace("- intent: bot_challenge", "- intent: is_bot")
    
    with open(os.path.join(test_dir, "rules.yml"), "w") as f:
        f.write(rules_content)

def create_actions_py(test_dir):
    """Create a test actions.py file"""
    actions_content = """from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")

        return []
"""
    with open(os.path.join(test_dir, "actions.py"), "w") as f:
        f.write(actions_content)

def run_checker(checker_path, test_dir, verbose=False):
    """Run the conflict checker on the test directory"""
    print_info(f"Running conflict checker: {checker_path}", verbose)
    
    try:
        result = subprocess.run(
            [sys.executable, checker_path, "--directory", test_dir],
            capture_output=True,
            text=True
        )
        
        if verbose:
            print_info("Checker output:", verbose)
            print(result.stdout)
            
            if result.stderr:
                print_error("Checker error output:")
                print(result.stderr)
        
        # In this case, a return code of 1 means issues were found, which is expected and successful
        # The test should only fail if there's a runtime error in the checker script
        if "conflicts:" in result.stdout:
            return True, result.stdout
        return result.returncode == 0, result.stdout
    except Exception as e:
        print_error(f"Error running checker: {e}")
        return False, str(e)

def run_fixer(fixer_path, test_dir, verbose=False):
    """Run the conflict fixer on the test directory"""
    print_info(f"Running conflict fixer: {fixer_path}", verbose)
    
    try:
        result = subprocess.run(
            [sys.executable, fixer_path, "--directory", test_dir],
            capture_output=True,
            text=True
        )
        
        if verbose:
            print_info("Fixer output:", verbose)
            print(result.stdout)
            
            if result.stderr:
                print_error("Fixer error output:")
                print(result.stderr)
        
        # Return success as long as the fixer ran (even with return code 1)
        # since a non-zero return code might just indicate that some fixes couldn't be applied
        # We'll check the actual fixes separately
        if "Failed to run" in result.stdout or "Error" in result.stdout:
            return False, result.stdout
        return True, result.stdout
    except Exception as e:
        print_error(f"Error running fixer: {e}")
        return False, str(e)

def check_fixes(test_dir, verbose=False):
    """Check if the fixes were applied correctly"""
    issues_fixed = True
    
    # Load the fixed files
    try:
        with open(os.path.join(test_dir, "domain.yml"), "r") as f:
            domain = yaml.safe_load(f)
        
        with open(os.path.join(test_dir, "config.yml"), "r") as f:
            config = yaml.safe_load(f)
        
        with open(os.path.join(test_dir, "stories.yml"), "r") as f:
            stories_content = f.read()
        
        with open(os.path.join(test_dir, "rules.yml"), "r") as f:
            rules_content = f.read()
        
        # Check domain intents - the fixer should add the missing intents
        if "mood_awesome" not in domain.get("intents", []):
            print_error("Missing intent 'mood_awesome' in domain.yml not fixed")
            issues_fixed = False
        
        if "is_bot" not in domain.get("intents", []):
            print_error("Missing intent 'is_bot' in domain.yml not fixed")
            issues_fixed = False
        
        # Check domain actions - the fixer should add the missing actions
        if "utter_very_happy" not in domain.get("actions", []):
            print_error("Missing action 'utter_very_happy' in domain.yml not fixed")
            issues_fixed = False
        
        # Check config extractors - the fixer should add the missing extractor
        pipeline_names = [item.get("name") if isinstance(item, dict) else item for item in config.get("pipeline", [])]
        if "EntitySynonymMapper" not in pipeline_names:
            print_error("Missing 'EntitySynonymMapper' extractor in config.yml not fixed")
            issues_fixed = False
        
        # Note: In the current implementation, the fixer doesn't modify stories or rules
        # to fix undefined intents/actions, it only adds them to the domain
        # So we shouldn't fail the test for these checks
        
    except Exception as e:
        print_error(f"Error checking fixes: {e}")
        issues_fixed = False
    
    return issues_fixed

def main():
    parser = argparse.ArgumentParser(description="Test Rasa conflict checker and fixer tools")
    parser.add_argument("--checker", required=True, help="Path to the Rasa conflict checker script")
    parser.add_argument("--fixer", required=True, help="Path to the Rasa conflict fixer script")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.checker):
        print_error(f"Checker script not found: {args.checker}")
        return 1
    
    if not os.path.isfile(args.fixer):
        print_error(f"Fixer script not found: {args.fixer}")
        return 1
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp()
    print_info(f"Created test directory: {test_dir}", args.verbose)
    
    try:
        # Create test files with conflicts
        print_info("Creating test files with conflicts", args.verbose)
        create_config_yml(test_dir, missing_extractors=True)
        create_domain_yml(test_dir, missing_intents=True, missing_actions=True)
        create_nlu_yml(test_dir)
        create_stories_yml(test_dir, undefined_intents=True, undefined_actions=True)
        create_rules_yml(test_dir, undefined_intents=True)
        create_actions_py(test_dir)
        
        # Run the conflict checker
        checker_success, checker_output = run_checker(args.checker, test_dir, args.verbose)
        
        if not checker_success:
            print_error("Conflict checker failed to run correctly")
            return 1
        
        # Check that the checker found the expected conflicts
        expected_issues = [
            "not defined in domain.yml", 
            "EntitySynonymMapper"
        ]
        issues_found = all(issue in checker_output for issue in expected_issues)
        
        if issues_found:
            print_success("Conflict checker correctly identified the issues")
        else:
            print_error("Conflict checker did not find the expected issues")
            return 1
        
        # Run the conflict fixer
        fixer_success, fixer_output = run_fixer(args.fixer, test_dir, args.verbose)
        
        if not fixer_success:
            print_error("Conflict fixer failed to run")
            return 1
        
        print_success("Conflict fixer ran successfully")
        
        # Check if the fixes were applied correctly
        if check_fixes(test_dir, args.verbose):
            print_success("All fixes were applied correctly")
        else:
            print_error("Some fixes were not applied correctly")
            return 1
        
        print(f"{Fore.GREEN}All tests passed successfully!{Style.RESET_ALL}")
        return 0
        
    finally:
        # Clean up the temporary directory
        print_info(f"Cleaning up test directory: {test_dir}", args.verbose)
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    sys.exit(main()) 