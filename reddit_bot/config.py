import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Reddit bot settings"""
    
    # Reddit API credentials
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USERNAME = os.getenv('REDDIT_USERNAME')
    REDDIT_PASSWORD = os.getenv('REDDIT_PASSWORD')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'ImageBot/1.0')
    
    # Default settings
    DEFAULT_SUBREDDIT = os.getenv('DEFAULT_SUBREDDIT', 'test')
    
    # Supported image formats
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Max file size (in MB)
    MAX_FILE_SIZE_MB = 20
    
    @classmethod
    def validate(cls):
        """Validate that all required credentials are set"""
        required_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET', 
            'REDDIT_USERNAME',
            'REDDIT_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
