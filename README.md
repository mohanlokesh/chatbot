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
- Python 3.12.1

## Prerequisites

- Python 3.12.1
- PostgreSQL database
- Rasa and Rasa SDK

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - Mac/Linux:
     ```
     source venv/bin/activate
     ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Configure your PostgreSQL connection:
   - Create a PostgreSQL database
   - Update the `.env` file with your database credentials:
     ```
     DATABASE_URL="postgresql://username:password@host:port/database_name"
     ```
6. Setup the database:
   ```
   python database/setup_db.py
   python database/migrate_orders.py --orders 5
   ```
7. Train the Rasa model:
   ```
   python start_rasa_bot.py --train
   ```
8. Run the complete application with one command:
   ```
   python app.py
   ```
   
   This will start:
   - Flask backend server
   - Streamlit frontend
   - Rasa server and action server

   For separate components:
   ```
   # Run only backend
   python app.py --backend-only
   
   # Run only frontend
   python app.py --frontend-only
   
   # Run only Rasa bot
   python app.py --rasa-only
   ```

## Project Structure

- `/frontend`: Streamlit UI components
- `/backend`: Flask API and server logic
- `/database`: Database models and scripts
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