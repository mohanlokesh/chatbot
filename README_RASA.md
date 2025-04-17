# Using Rasa with AI Chatbot

This guide explains how to use the Rasa integration in the AI Chatbot project.

## Overview

The AI Chatbot project now includes integration with Rasa, a powerful open-source framework for building conversational AI applications. Rasa provides advanced natural language understanding (NLU) capabilities and dialogue management.

## Setup

### 1. Install Dependencies

Make sure you have installed all the required dependencies:

```bash
pip install -r requirements.txt
```

This will install both Rasa and Rasa SDK, along with all the other required packages.

### 2. Initialize Rasa (First Time Setup)

The Rasa files are already set up in the `ai_chatbot/rasa_bot` directory. However, if you need to initialize Rasa from scratch, you can run:

```bash
cd ai_chatbot/rasa_bot
rasa init
```

This will create a new Rasa project. You would then need to copy over or adapt our configuration files.

## Training the Rasa Model

Before using Rasa, you need to train the model:

```bash
python ai_chatbot/start_rasa_bot.py --train
```

This will:
1. Seed Rasa with examples from our database
2. Train a new Rasa model with the provided training data

Alternatively, you can train Rasa directly:

```bash
cd ai_chatbot/rasa_bot
rasa train
```

## Starting the Rasa Servers

To start the Rasa server and the action server:

```bash
python ai_chatbot/start_rasa_bot.py
```

This will start:
- Rasa server on port 5005
- Action server on port 5055

## Using Rasa with the Chatbot

The Chatbot class automatically uses Rasa if available. When you create a new Chatbot instance, it will try to use Rasa for NLP processing:

```python
from models.chatbot import Chatbot

# Create a new chatbot with Rasa (default)
chatbot = Chatbot()

# Or explicitly enable/disable Rasa
chatbot = Chatbot(use_rasa=True)  # Use Rasa if available
chatbot = Chatbot(use_rasa=False)  # Use only transformer-based processing
```

The `process_message` method will first try to use Rasa for processing, and fall back to the transformer-based approach if Rasa is not available or fails.

## Rasa Configuration Files

The Rasa integration includes the following configuration files:

- `config.yml`: NLU pipeline and policy configuration
- `domain.yml`: Domain specification with intents, entities, and responses
- `data/nlu/nlu.yml`: Training data for NLU
- `data/stories/stories.yml`: Conversation flows
- `data/rules/rules.yml`: Rules for specific conversation patterns
- `actions/actions.py`: Custom actions that integrate with the project database
- `endpoints.yml`: Endpoint configuration

## Customizing Rasa

To customize the Rasa integration:

1. **Add new intents**: Edit `data/nlu/nlu.yml` to add new example sentences
2. **Add new responses**: Edit `domain.yml` to add new response templates
3. **Create new conversation flows**: Edit `data/stories/stories.yml`
4. **Add custom actions**: Edit `actions/actions.py`

After making changes, re-train the model:

```bash
python ai_chatbot/start_rasa_bot.py --train
```

## Seeding Rasa from Database

The system can automatically generate training examples from the support data in the database:

```bash
python ai_chatbot/start_rasa_bot.py --seed-only
```

This will create a file `data/nlu/database_examples.yml` with examples from the database.

## Testing Rasa Directly

You can interact with Rasa directly using the Rasa shell:

```bash
cd ai_chatbot/rasa_bot
rasa shell
```

Or test NLU only:

```bash
rasa shell nlu
```

## Troubleshooting

If you encounter issues with Rasa:

1. **Check dependencies**: Make sure all required packages are installed
2. **Check server status**: Ensure both the Rasa server and action server are running
3. **Check logs**: Look for error messages in the console output
4. **Retrain the model**: Delete the `models` directory in `rasa_bot` and retrain

## Resources

- [Rasa Documentation](https://rasa.com/docs/)
- [Rasa GitHub Repository](https://github.com/RasaHQ/rasa) 