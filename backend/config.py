import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here' # IMPORTANT: Change this in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key' # IMPORTANT: Change this too
    # Numista API credentials - MUST be set via environment variables
    # Do NOT commit API keys to version control!
    NUMISTA_API_KEY = os.environ.get('NUMISTA_API_KEY')  # Required: Set in environment or .env file
    NUMISTA_CLIENT_ID = os.environ.get('NUMISTA_CLIENT_ID')  # Required: Set in environment or .env file