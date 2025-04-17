# Chatbot Training Data

This directory contains training data and tools for the AI Chatbot system.

## Available Data Tools

The AI Chatbot system provides several tools to generate, manage, and import training data:

1. **Manual Dataset Tool** (`manual_dataset.py`): Add pre-defined or custom datasets manually
2. **Automated Dataset Tool** (`auto_dataset.py`): Generate data through web scraping and synthetic generation
3. **Custom Dataset Template** (`custom_dataset_template.json`): Template for creating your own datasets

## Using the Manual Dataset Tool

The manual dataset tool allows you to add pre-defined, high-quality datasets to your chatbot's knowledge base.

```bash
# Add all available manual datasets
python manual_dataset.py --all

# Add only e-commerce data
python manual_dataset.py --ecommerce

# Add customer support data
python manual_dataset.py --support

# Add technical support data
python manual_dataset.py --technical

# Add product data
python manual_dataset.py --product

# Add custom data from a JSON file
python manual_dataset.py --custom path/to/your/data.json --company "Your Company Name"
```

## Using the Automated Dataset Tool

The automated tool can scrape websites for FAQs or generate synthetic data for training.

```bash
# Run all automated data collection methods
python auto_dataset.py --all

# Scrape e-commerce websites only
python auto_dataset.py --ecommerce

# Scrape customer support websites only
python auto_dataset.py --support

# Scrape a specific URL
python auto_dataset.py --url "https://example.com/faq" --company "Example Company" --category "General"

# Generate synthetic data (creates JSON file but doesn't add to database)
python auto_dataset.py --synthetic --synthetic-count 100

# Generate synthetic data and add to database
python auto_dataset.py --synthetic --add-synthetic --synthetic-count 100 --synthetic-company "My Synthetic Data"
```

## Creating Custom Datasets

You can create your own custom datasets using the template provided:

1. Copy `custom_dataset_template.json` to a new file (e.g., `my_company_data.json`)
2. Edit the file to include your own questions, answers, and categories
3. Import using:
   ```bash
   python manual_dataset.py --custom my_company_data.json --company "My Company Name"
   ```

The JSON format is an array of objects with the following structure:

```json
[
  {
    "question": "Your question here?",
    "answer": "Your detailed answer here.",
    "category": "General"  // Optional, defaults to "General"
  },
  // Add more items...
]
```

## Data Categories

When creating your own datasets, consider using these standard categories for better organization:

- General
- Account
- Billing
- Payments
- Orders
- Shipping
- Returns
- Products
- Technical
- Security
- Contact
- Support
- Services

## Best Practices

1. **Quality over Quantity**: Add fewer, high-quality examples rather than many low-quality ones
2. **Diverse Questions**: Include different ways people might ask the same question
3. **Detailed Answers**: Provide comprehensive answers that fully address the questions
4. **Update Regularly**: Add new data as products, policies, or services change
5. **Test**: After adding data, test the chatbot to ensure it provides appropriate responses

## Viewing Dataset Statistics

You can view statistics about your training data using:

```bash
python train_chatbot.py --stats
```

This will show counts of data items by company and in total. 