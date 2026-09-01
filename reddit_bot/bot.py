import praw
import os
import sys
from pathlib import Path
from PIL import Image
import requests
from reddit_bot.config import Config

class RedditImageBot:
    """Reddit bot for uploading images with titles and descriptions"""
    
    def __init__(self):
        """Initialize the Reddit bot with API credentials"""
        try:
            Config.validate()
            self.reddit = praw.Reddit(
                client_id=Config.REDDIT_CLIENT_ID,
                client_secret=Config.REDDIT_CLIENT_SECRET,
                username=Config.REDDIT_USERNAME,
                password=Config.REDDIT_PASSWORD,
                user_agent=Config.REDDIT_USER_AGENT
            )
            print(f"Successfully authenticated as: {self.reddit.user.me()}")
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise
    
    def validate_image(self, image_path):
        """Validate image file and format"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Check file extension
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in Config.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {file_ext}. Supported: {Config.SUPPORTED_FORMATS}")
        
        # Check file size
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if file_size_mb > Config.MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB. Max size: {Config.MAX_FILE_SIZE_MB}MB")
        
        # Validate image can be opened
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")
        
        return True
    
    def validate_subreddit(self, subreddit_name):
        """Validate subreddit exists and is accessible"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            # Try to access subreddit info to check if it exists
            _ = subreddit.display_name
            return subreddit
        except Exception as e:
            raise ValueError(f"Cannot access subreddit '{subreddit_name}': {e}")
    
    def post_image(self, image_path, title, subreddit_name, description="", flair_text=None):
        """
        Post an image to a subreddit with title and description
        
        Args:
            image_path (str): Path to the image file
            title (str): Post title
            subreddit_name (str): Target subreddit name
            description (str): Optional description text
            flair_text (str): Optional flair text
        
        Returns:
            str: URL of the created post
        """
        try:
            # Validate inputs
            self.validate_image(image_path)
            subreddit = self.validate_subreddit(subreddit_name)
            
            if not title.strip():
                raise ValueError("Title cannot be empty")
            
            print(f"Uploading image to r/{subreddit_name}...")
            
            # Create the post
            submission = subreddit.submit_image(
                title=title.strip(),
                image_path=image_path
            )
            
            # Add description as a comment if provided
            if description.strip():
                print("Adding description comment...")
                comment = submission.reply(description.strip())
                # Pin the comment (if user has mod permissions)
                try:
                    comment.mod.distinguish(how='yes', sticky=True)
                    print("Description comment pinned")
                except:
                    print("Description comment added (couldn't pin - no mod permissions)")
            
            # Add flair if provided and available
            if flair_text:
                try:
                    # Get available flairs
                    flairs = list(subreddit.flair.link_templates)
                    matching_flair = None
                    
                    for flair in flairs:
                        if flair['text'].lower() == flair_text.lower():
                            matching_flair = flair
                            break
                    
                    if matching_flair:
                        submission.flair.select(matching_flair['id'])
                        print(f"Applied flair: {flair_text}")
                    else:
                        print(f"Flair '{flair_text}' not found in subreddit")
                        
                except Exception as e:
                    print(f"Could not apply flair: {e}")
            
            post_url = f"https://reddit.com{submission.permalink}"
            print(f"Successfully posted! URL: {post_url}")
            
            return post_url
            
        except Exception as e:
            print(f"Failed to post image: {e}")
            raise
    
    def get_subreddit_info(self, subreddit_name):
        """Get information about a subreddit"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            info = {
                'name': subreddit.display_name,
                'title': subreddit.title,
                'description': subreddit.description[:200] + '...' if len(subreddit.description) > 200 else subreddit.description,
                'subscribers': subreddit.subscribers,
                'rules_count': len(list(subreddit.rules())),
                'submission_type': subreddit.submission_type,
                'allow_images': subreddit.submission_type in ['any', 'link']
            }
            
            return info
            
        except Exception as e:
            raise ValueError(f"Could not get subreddit info: {e}")
    
    def list_user_posts(self, limit=10):
        """List recent posts by the authenticated user"""
        try:
            posts = []
            for submission in self.reddit.user.me().submissions.new(limit=limit):
                posts.append({
                    'title': submission.title,
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'url': f"https://reddit.com{submission.permalink}",
                    'created': submission.created_utc
                })
            return posts
        except Exception as e:
            print(f"Could not fetch user posts: {e}")
            return []
