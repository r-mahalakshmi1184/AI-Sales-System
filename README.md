# AI-Sales-System
AI-powered store transaction query system. Retrieve transaction records and sales summaries using natural language or manual filters. Supports intelligent date, customer, item, and transaction-type detection.  README.md:
AI-powered system to query store transactions using natural language or manual filters. Retrieve detailed transaction data or summarized sales reports directly from your database.

## Features
- Natural language queries for store transactions
- Manual filter support (customer, item, transaction type, date)
- AI extraction of filters from user input
- Sales summary generation
- SQLite database backend
- Flask web interface
- Optional production deployment using Waitress

## Requirements
- Python 3.8+
- Flask
- spaCy (`en_core_web_sm`)
- SQLite3 (built-in)
- Waitress (optional for production)
- CSV file for initial data

Install packages:

```bash
pip install Flask spacy waitress
python -m spacy download en_core_web_sm
