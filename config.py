import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Use PostgreSQL in production, SQLite in development
    if os.environ.get('DATABASE_URL'):
        # Render uses postgresql:// but SQLAlchemy needs postgresql://
        database_url = os.environ.get('DATABASE_URL')
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///expense_tracker.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
