# AI-Driven Chatbot System with Rasa and PostgreSQL

An intelligent chatbot system for Customer Support / E-commerce that can understand user queries using Rasa NLP, retrieve answers from PostgreSQL database, and learn from interactions.

## Features

- User authentication (login/register)
- Real-time chat interface
- Dynamic query resolution using PostgreSQL database
- Rasa NLP for intent detection and entity extraction
- Custom actions for database integration
- Order status tracking and information retrieval
- User session tracking

## Technology Stack

- Frontend: Streamlit
- Backend: Flask
- NLP: Rasa 3.6.16
- Database: PostgreSQL
- Python 3.9.13

## Prerequisites

- Python 3.9.13
- PostgreSQL database (installed and running)
- Git (for cloning the repository)

## Step-by-Step Setup Guide for Windows

### 1. Install Required Software

1. **Install Python 3.9.13**:
   - Download Python 3.9.13 from [python.org](https://www.python.org/downloads/release/python-3913/)
   - During installation, ensure you check "Add Python to PATH"
   - Verify installation by opening Command Prompt and typing:
     ```
     python --version
     ```

2. **Install PostgreSQL**:
   - Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
   - Remember the password you set for the postgres user
   - Install pgAdmin if you want a GUI to manage your database (comes with the installer)

3. **Create a PostgreSQL Database**:
   - Open pgAdmin or use the psql command line tool
   - Create a new database named `ai_chatbot`:
     ```
     CREATE DATABASE ai_chatbot;
     ```

### 2. Setup the Project

1. **Clone the Repository**:
   ```
   git clone <repository-url>
   cd ai_chatbot
   ```

2. **Create a Virtual Environment**:
   ```
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   ```
   venv\Scripts\activate
   ```

4. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```
   
   If you encounter errors, try installing packages individually:
   ```
   pip install flask==3.0.0 flask-cors==4.0.0 sqlalchemy==1.4.46 rasa==3.6.16 rasa-sdk==3.6.2 psycopg2-binary==2.9.9
   pip install streamlit==1.34.0 scikit-learn==1.1.3 nltk==3.8.1 python-dotenv==1.0.1
   pip install bcrypt==4.1.2 pyjwt==2.8.0 pandas<2.0.0 alembic==1.13.1
   ```

5. **Configure PostgreSQL Connection**:
   - Create or edit the `.env` file in the project root:
     ```
     DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/ai_chatbot"
     JWT_SECRET_KEY="your_secret_key"
     PORT=5000
     API_URL="http://localhost:5000/api"
     STEREAMLIT_SERVER_PORT=8501
     ```
   - Replace `yourpassword` with your PostgreSQL password

### 3. Initialize the Database

1. **Setup Database Schema**:
   ```
   python database/setup_db.py
   ```

2. **Create Sample Orders** (for testing):
   ```
   python database/migrate_orders.py --orders 5
   ```

3. **Organize Training Data** (optional):
   ```
   python utils/organize_training_data.py
   ```
   This will organize all JSON training files into the `data/training` directory.

### 4. Train and Start Rasa

1. **Train the Rasa Model**:
   ```
   python start_rasa_bot.py --train
   ```
   This will train the model using the provided NLU examples and conversation flows.

2. **Test Rasa Connection** (optional):
   ```
   python start_rasa_bot.py --seed-only
   ```
   This verifies the connection to PostgreSQL and seeds Rasa with data from the database.

### 5. Run the Application

There are three ways to run the application:

#### Option 1: Run Everything at Once
```
python app.py
```
This starts the backend server, frontend, and Rasa bot all together.

#### Option 2: Run Components Separately
Open three separate Command Prompt windows, activate the virtual environment in each, and run:

1. **Backend Server**:
   ```
   python app.py --backend-only
   ```

2. **Rasa Bot**:
   ```
   python app.py --rasa-only
   ```

3. **Frontend**:
   ```
   python app.py --frontend-only
   ```

#### Option 3: Run Original Scripts
Open three separate Command Prompt windows, activate the virtual environment in each, and run:

1. **Backend**:
   ```
   python start_backend.py
   ```

2. **Rasa Bot**:
   ```
   python start_rasa_bot.py
   ```

3. **Frontend**:
   ```
   python start_frontend.py
   ```

### 6. Access the Application

- Frontend: http://localhost:8501
- Backend API: http://localhost:5000/api
- Rasa API: http://localhost:5005

### Default Login Credentials
- Username: admin
- Password: password123

## Troubleshooting

### Common Issues on Windows

1. **PostgreSQL Connection Error**:
   - Ensure PostgreSQL service is running (check Services app)
   - Verify your DATABASE_URL in the .env file has the correct password and port
   - Try connecting with pgAdmin to confirm your credentials work

2. **Port Already in Use**:
   - If you see "Port already in use" errors, find and close the application using that port
   - You can use Task Manager to find Python processes
   - Alternatively, change the port in the command: `python app.py --port 5001`

3. **Rasa Startup Issues**:
   - If Rasa fails to start, try running the action server and Rasa server separately:
     ```
     cd rasa_bot
     rasa run actions --port 5055
     ```
     And in another window:
     ```
     cd rasa_bot
     rasa run --enable-api --cors "*" --port 5005
     ```

4. **Package Installation Errors**:
   - If you face dependency conflicts, try creating a fresh virtual environment
   - For issues with specific packages like `psycopg2-binary`, try installing Visual C++ Build Tools

5. **Command Not Found Errors**:
   - If Windows doesn't recognize commands like `rasa`, ensure you've activated the virtual environment
   - Try using the full path: `python -m rasa run` instead of just `rasa run`

## Project Structure

- `/frontend`: Streamlit UI components
- `/backend`: Flask API and server logic
- `/database`: Database models and scripts
- `/data/training`: JSON training data sources
- `/rasa_bot`: Rasa chatbot configuration and training data
  - `/actions`: Custom actions that integrate with PostgreSQL
  - `/data`: NLU training data, stories, and rules
  - `/models`: Trained Rasa models
- `/utils`: Utility functions and helpers

## Rasa Custom Actions

The chatbot includes several custom actions that integrate with the PostgreSQL database:

1. **Check Order Status**: Retrieves order status information from the database
2. **List Order Items**: Lists all items in a specific order
3. **Get User Orders**: Retrieves all orders for a specific user

## Database Schema

The PostgreSQL database includes the following main tables:

- `users`: User information
- `orders`: Order information
- `order_items`: Items contained in each order
- `conversations`: Chat conversation history
- `messages`: Individual messages in conversations

## Troubleshooting

If you encounter issues:

1. Check your PostgreSQL connection
2. Ensure Rasa is installed correctly
3. Look at the console output for error messages
4. Make sure all required ports are available (5000, 5005, 5055, 8501)

# Rasa Conflict Testing Tools

This repository contains tools for checking and fixing inconsistencies in Rasa project files.

## Test Script

The `test_rasa_tools.py` script is designed to verify the functionality of the Rasa conflict checker and fixer tools. It creates a set of test files with deliberate conflicts and verifies that:

1. The conflict checker correctly identifies all issues
2. The conflict fixer properly resolves the identified issues

### Prerequisites

Make sure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
```

### Usage

To run the test script:

```bash
python test_rasa_tools.py
```

Optional arguments:
- `--verbose`: Enable verbose output
- `--checker-script`: Path to the checker script (default: "check_rasa_conflicts.py")
- `--fixer-script`: Path to the fixer script (default: "fix_rasa_conflicts.py")

Example with custom script paths:
```bash
python test_rasa_tools.py --checker-script ./scripts/check.py --fixer-script ./scripts/fix.py --verbose
```

### Test Cases

The script creates test files with these deliberate conflicts:
- Missing intents and actions in domain.yml
- Intents in nlu.yml not defined in domain.yml
- Undefined actions in stories.yml
- Missing RegexEntityExtractor in config.yml
- Missing action class in actions.py

## Expected Results

When running the test script:
1. The checker should identify all conflicts
2. The fixer should resolve all conflicts
3. A second run of the checker should find no remaining issues

## Troubleshooting

If the tests fail:
- Check that your checker and fixer scripts are accessible
- Verify that all dependencies are installed
- Use the `--verbose` flag for more detailed output

## License

MIT

# Rasa Tools Tester

This script tests the functionality of Rasa conflict checker and fixer tools by:
1. Creating test files with deliberate conflicts
2. Running the checker to detect conflicts
3. Running the fixer to resolve conflicts
4. Verifying that the fixes were applied correctly

## Usage

```bash
python test_rasa_tools.py --checker path/to/checker.py --fixer path/to/fixer.py --verbose
```

### Arguments

- `--checker`: Path to the Rasa conflict checker script (required)
- `--fixer`: Path to the Rasa conflict fixer script (required)
- `--verbose`: Enable verbose output (optional)

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Example

```bash
python test_rasa_tools.py --checker rasa_conflict_checker.py --fixer rasa_conflict_fixer.py --verbose
```

The script will:
- Create temporary test files with conflicts
- Run the conflict checker
- Run the conflict fixer
- Verify if the fixes were correctly applied
- Report the results
- Clean up temporary files

## Conflicts Tested

1. Missing intents in domain.yml
2. Missing actions in domain.yml
3. Missing extractors in config.yml
4. Undefined actions in stories.yml
5. Undefined intents in stories.yml and rules.yml 