# Reddit Image Bot

A powerful and user-friendly bot for efficiently uploading images to Reddit with titles and descriptions. Features both command-line and graphical user interfaces.

## Features

- **Easy Image Uploads**: Upload images to any subreddit with title and description
- **Multiple Interfaces**: Choose between CLI, GUI, or interactive modes
- **Smart Validation**: Automatic image format and size validation
- **Subreddit Info**: Get subreddit information and rules
- **Post History**: View your recent posts
- **Flair Support**: Add flairs to your posts (when available)
- **Auto-pinned Descriptions**: Descriptions are posted as comments and pinned when possible
- **Error Handling**: Comprehensive error handling and user feedback

## Project Structure

```
Reddit-bot/
├── reddit_bot/            # Core library
│   ├── config.py          # Credential loading and settings
│   ├── bot.py              # RedditImageBot - single image posting
│   └── automation.py       # AutomatedRedditBot - batch/scheduled posting
├── tests/
│   └── test_connection.py # Standalone credential/connection check
├── cli_interface.py       # CLI entry point
├── gui_interface.py       # GUI entry point
├── .env.example           # Copy to .env and fill in credentials
└── requirements.txt
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Reddit API Setup

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the form:
   - **Name**: Your bot name (e.g., "My Image Bot")
   - **Description**: Brief description
   - **About URL**: Can be blank
   - **Redirect URI**: http://localhost:8080 (required but not used)

5. Note down your credentials:
   - **Client ID**: The string under your app name
   - **Client Secret**: The "secret" field

### 3. Configure Credentials

Create a `.env` file in the project directory:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=ImageBot/1.0 by YourUsername
DEFAULT_SUBREDDIT=test
```

> **Tip**: Copy `.env.example` and rename it to `.env`, then fill in your credentials.

## Usage

### GUI Mode (Recommended)

```bash
python gui_interface.py
```

The GUI provides an intuitive interface with:
- Image browser with drag-and-drop
- Auto-title generation from filename
- Subreddit information lookup
- Post history viewer
- Progress tracking

### Interactive CLI Mode

```bash
python cli_interface.py
```

Features an interactive command prompt with commands:
- `post` - Post a new image
- `info` - Get subreddit information
- `history` - View recent posts
- `help` - Show available commands
- `quit` - Exit

### Command Line Mode

```bash
# Basic usage
python cli_interface.py --image photo.jpg --title "My Amazing Photo" --subreddit pics

# With description and flair
python cli_interface.py --image photo.jpg --title "My Photo" --subreddit pics --description "This is my awesome photo!" --flair "OC"
```

### Direct API Usage

```python
from reddit_bot.bot import RedditImageBot

bot = RedditImageBot()
post_url = bot.post_image(
    image_path="my_image.jpg",
    title="My Post Title",
    subreddit_name="pics",
    description="Optional description",
    flair_text="OC"
)
print(f"Posted at: {post_url}")
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

**File Size Limit**: 20MB (Reddit's limit)

## Configuration Options

Edit `config.py` to customize:

- `SUPPORTED_FORMATS`: Allowed image formats
- `MAX_FILE_SIZE_MB`: Maximum file size in MB
- `DEFAULT_SUBREDDIT`: Default subreddit for posts

## Commands Reference

### CLI Arguments

| Argument | Short | Description | Example |
|----------|-------|-------------|---------|
| `--image` | `-i` | Path to image file | `-i photo.jpg` |
| `--title` | `-t` | Post title | `-t "My Photo"` |
| `--subreddit` | `-s` | Target subreddit | `-s pics` |
| `--description` | `-d` | Post description | `-d "Description"` |
| `--flair` | `-f` | Post flair | `-f "OC"` |
| `--interactive` | | Force interactive mode | `--interactive` |

### Interactive Commands

| Command | Description |
|---------|-------------|
| `post` | Create a new post |
| `info` | Get subreddit information |
| `history` | View your recent posts |
| `help` | Show available commands |
| `quit`/`exit` | Exit the program |

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Check your `.env` file exists and has correct credentials
- Verify your Reddit username and password are correct
- Ensure your app is set to "script" type in Reddit preferences

**"File too large"**
- Reddit has a 20MB limit for images
- Compress your image or use a different format

**"Subreddit not found"**
- Check subreddit name spelling
- Ensure the subreddit exists and is public
- Some subreddits may restrict new accounts

**"Cannot access subreddit"**
- You might be banned from the subreddit
- The subreddit might be private
- Check if the subreddit allows image posts

## Security Notes

- Never commit your `.env` file to version control
- Use a dedicated Reddit account for bot activities
- Be aware of Reddit's API rate limits
- Follow subreddit rules and Reddit's terms of service

## API Rate Limits

Reddit's API has rate limits:
- ~60 requests per minute for authenticated users
- The bot includes automatic error handling for rate limits
- Space out your posts to avoid hitting limits

## Contributing

Feel free to submit issues, feature requests, or pull requests!

## License

This project is open source. Please respect Reddit's Terms of Service and API guidelines when using this bot.

---

**Happy Posting!**

For support or questions, please open an issue on the repository.
