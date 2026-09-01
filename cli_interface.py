#!/usr/bin/env python3
"""
Reddit Image Bot - CLI Interface
Simple command-line interface for uploading images to Reddit
"""

import argparse
import sys
import os
from pathlib import Path
from reddit_bot.bot import RedditImageBot
from reddit_bot.config import Config

def print_banner():
    """Print application banner"""
    print("Reddit Image Bot")
    print("=" * 50)

def interactive_mode():
    """Interactive mode for posting images"""
    print("\nInteractive Mode")
    print("Type 'quit' or 'exit' to stop, 'help' for commands\n")

    try:
        bot = RedditImageBot()
    except Exception:
        sys.exit(1)
    
    while True:
        try:
            command = input("Bot> ").strip().lower()
            
            if command in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            elif command == 'help':
                print_help()
                continue
            
            elif command == 'post':
                interactive_post(bot)
                
            elif command == 'info':
                interactive_subreddit_info(bot)
                
            elif command == 'history':
                show_user_history(bot)
                
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def print_help():
    """Print help information"""
    print("\nAvailable Commands:")
    print("  post     - Post a new image")
    print("  info     - Get subreddit information")
    print("  history  - Show your recent posts")
    print("  help     - Show this help")
    print("  quit/exit - Exit the program")

def interactive_post(bot):
    """Interactive image posting"""
    try:
        # Get image path
        image_path = input("Image path: ").strip().strip('"\'')
        if not image_path:
            print("Image path is required")
            return
        
        # Expand user path
        image_path = os.path.expanduser(image_path)
        
        # Get title
        title = input("Post title: ").strip()
        if not title:
            print("Title is required")
            return
        
        # Get subreddit
        subreddit = input(f"Subreddit (default: {Config.DEFAULT_SUBREDDIT}): ").strip()
        if not subreddit:
            subreddit = Config.DEFAULT_SUBREDDIT
        
        # Get description
        description = input("Description (optional): ").strip()
        
        # Get flair
        flair = input("Flair (optional): ").strip()
        
        # Confirm before posting
        print(f"\nPost Summary:")
        print(f"   Image: {image_path}")
        print(f"   Title: {title}")
        print(f"   Subreddit: r/{subreddit}")
        if description:
            print(f"   Description: {description[:50]}{'...' if len(description) > 50 else ''}")
        if flair:
            print(f"   Flair: {flair}")
        
        confirm = input("\nPost this image? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Post cancelled")
            return
        
        # Post the image
        post_url = bot.post_image(
            image_path=image_path,
            title=title,
            subreddit_name=subreddit,
            description=description,
            flair_text=flair if flair else None
        )
        
        print(f"\nSuccess! Your post is live at: {post_url}")
        
    except Exception as e:
        print(f"Failed to post: {e}")

def interactive_subreddit_info(bot):
    """Get subreddit information interactively"""
    try:
        subreddit = input("Subreddit name: ").strip()
        if not subreddit:
            print("Subreddit name is required")
            return
        
        info = bot.get_subreddit_info(subreddit)
        
        print(f"\nSubreddit Info: r/{info['name']}")
        print(f"   Title: {info['title']}")
        print(f"   Subscribers: {info['subscribers']:,}")
        print(f"   Rules: {info['rules_count']}")
        print(f"   Allows Images: {'Yes' if info['allow_images'] else 'No'}")
        print(f"   Description: {info['description']}")
        
    except Exception as e:
        print(f"Error: {e}")

def show_user_history(bot):
    """Show user's recent post history"""
    try:
        posts = bot.list_user_posts(limit=5)
        if not posts:
            print("No recent posts found")
            return
        
        print("\nYour Recent Posts:")
        for i, post in enumerate(posts, 1):
            print(f"\n{i}. {post['title']}")
            print(f"   Subreddit: r/{post['subreddit']}")
            print(f"   Score: {post['score']}")
            print(f"   URL: {post['url']}")
            
    except Exception as e:
        print(f"Error: {e}")

def command_line_mode(args):
    """Command line mode for posting"""
    try:
        bot = RedditImageBot()
    except Exception:
        sys.exit(1)

    try:
        post_url = bot.post_image(
            image_path=args.image,
            title=args.title,
            subreddit_name=args.subreddit,
            description=args.description or "",
            flair_text=args.flair
        )
        print(f"Success! Posted at: {post_url}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Reddit Image Bot - Upload images to Reddit efficiently",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli_interface.py

  # Command line posting
  python cli_interface.py --image photo.jpg --title "My Photo" --subreddit pics

  # With description and flair
  python cli_interface.py --image photo.jpg --title "My Photo" --subreddit pics --description "This is my photo" --flair "OC"
        """
    )
    
    parser.add_argument('--image', '-i', help='Path to image file')
    parser.add_argument('--title', '-t', help='Post title')
    parser.add_argument('--subreddit', '-s', default=Config.DEFAULT_SUBREDDIT, help='Target subreddit')
    parser.add_argument('--description', '-d', help='Post description (posted as comment)')
    parser.add_argument('--flair', '-f', help='Post flair')
    parser.add_argument('--interactive', action='store_true', help='Force interactive mode')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check if we have required credentials
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print(f"\nPlease create a .env file with your Reddit API credentials.")
        print(f"See env_example.txt for the required format.")
        print(f"\nGet credentials at: https://www.reddit.com/prefs/apps")
        sys.exit(1)
    
    # Determine mode
    if args.interactive or not (args.image and args.title):
        interactive_mode()
    else:
        command_line_mode(args)

if __name__ == "__main__":
    main()
