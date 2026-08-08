import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    FLASK_APP = os.getenv('FLASK_APP', 'app')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Email Configuration (SMTP)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # Email Configuration (IMAP)
    IMAP_HOST = os.getenv('IMAP_HOST', 'imap.gmail.com')
    IMAP_USER = os.getenv('IMAP_USER')
    IMAP_PASSWORD = os.getenv('IMAP_PASSWORD')
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    MODEL_NAME = os.getenv('MODEL_NAME', 'llama3.2')
    
    @classmethod
    def validate_email_config(cls):
        """Validate that required email configuration is present"""
        required_vars = ['SMTP_USER', 'SMTP_PASSWORD', 'IMAP_USER', 'IMAP_PASSWORD']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required email configuration: {', '.join(missing)}")
    
    @classmethod
    def validate_ollama_config(cls):
        """Validate that required Ollama configuration is present"""
        if not cls.OLLAMA_BASE_URL:
            raise ValueError("Missing OLLAMA_BASE_URL configuration")
