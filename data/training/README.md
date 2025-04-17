# Training Data Organization

This directory contains JSON files with training data that can be used to enhance the Rasa chatbot. These files serve as a source for examples that can be converted to Rasa's YAML format or imported into the PostgreSQL database.

## Files and Their Purpose

- `custom_dataset_template.json`: Basic template with common customer service questions and answers
- `promo_code_variations.json`: Different ways users might ask about using promo codes
- `common_variations.json`: Various phrasings of common customer service queries
- `synthetic_data_50.json`: Synthetically generated data for broader coverage

## How to Use This Data

### Importing to PostgreSQL

1. Use the database import scripts to load this data into your PostgreSQL database:
   ```
   python database/import_training_data.py --file data/training/custom_dataset_template.json
   ```

### Converting to Rasa Format

1. The `utils/rasa_integration.py` file contains a `seed_rasa_from_database` method that can convert database entries into Rasa's NLU format
2. After importing the JSON data to PostgreSQL, run:
   ```
   python start_rasa_bot.py --seed-only
   ```

### Using as Reference

You can also use these files as a reference when manually creating Rasa NLU examples in the YAML format. The data patterns here can help you understand how to structure user queries and entity annotations.

## Extending the Data

When creating new training examples, consider:

1. Adding variations of the same question with different wordings
2. Including entity annotations like `[order_number](entity_name)` for Rasa to detect
3. Organizing examples by intent (question type)
4. Creating diverse examples that cover common user phrasing patterns 