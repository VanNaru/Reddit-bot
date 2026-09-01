#!/usr/bin/env python3
"""
Test script to verify Reddit connection independently
"""

import json
import os
from dotenv import load_dotenv

def test_reddit_connection():
    """Test Reddit API connection"""
    print("Testing Reddit Bot Connection...")
    
    # Load environment variables
    load_dotenv()
    
    # Check environment variables
    required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == f'your_{var.lower().replace("reddit_", "")}_here':
            missing_vars.append(var)
    
    if missing_vars:
        result = {
            "success": False,
            "username": None,
            "error": f"Missing or incomplete environment variables: {', '.join(missing_vars)}"
        }
        print("Environment Check Failed")
        print(json.dumps(result, indent=2))
        return result
    
    print("Environment variables configured")
    
    # Test importing required modules
    try:
        import praw
        print("PRAW library imported successfully")
    except ImportError as e:
        result = {
            "success": False,
            "username": None,
            "error": f"Failed to import PRAW: {str(e)}"
        }
        print("PRAW Import Failed")
        print(json.dumps(result, indent=2))
        return result
    
    # Test Reddit connection
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'TestBot/1.0')
        )
        
        # Test authentication
        username = str(reddit.user.me())
        print(f"Successfully authenticated as: {username}")
        
        result = {
            "success": True,
            "username": username,
            "error": None
        }
        print("Connection test successful!")
        print(json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        result = {
            "success": False,
            "username": None,
            "error": str(e)
        }
        print("Reddit API connection failed")
        print(json.dumps(result, indent=2))
        return result

if __name__ == "__main__":
    test_reddit_connection()
