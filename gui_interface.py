#!/usr/bin/env python3
"""
Reddit Image Bot - GUI Interface
Simple graphical interface for uploading images to Reddit
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import webbrowser
from pathlib import Path
from reddit_bot.bot import RedditImageBot
from reddit_bot.config import Config

class RedditBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit Image Bot")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Initialize bot
        self.bot = None
        
        # Setup GUI first
        self.setup_gui()
        
        # Then initialize bot (now that status_var exists)
        self.init_bot()
        
        # Load settings
        self.load_settings()
    
    def init_bot(self):
        """Initialize Reddit bot"""
        try:
            Config.validate()
            self.bot = RedditImageBot()
            self.status_var.set("Connected to Reddit")
        except Exception as e:
            self.status_var.set(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to Reddit:\n{e}\n\nPlease check your .env file.")
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Status bar
        self.status_var = tk.StringVar(value="Initializing...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Reddit Image Bot", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Image selection
        img_frame = ttk.LabelFrame(main_frame, text="Image Selection", padding="10")
        img_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.image_path_var = tk.StringVar()
        ttk.Entry(img_frame, textvariable=self.image_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(img_frame, text="Browse", command=self.browse_image).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Post details
        details_frame = ttk.LabelFrame(main_frame, text="Post Details", padding="10")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        ttk.Label(details_frame, text="Title:").pack(anchor=tk.W)
        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(details_frame, textvariable=self.title_var, width=50)
        title_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Subreddit
        subreddit_frame = ttk.Frame(details_frame)
        subreddit_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(subreddit_frame, text="Subreddit:").pack(anchor=tk.W)
        subreddit_input_frame = ttk.Frame(subreddit_frame)
        subreddit_input_frame.pack(fill=tk.X)
        
        ttk.Label(subreddit_input_frame, text="r/").pack(side=tk.LEFT)
        self.subreddit_var = tk.StringVar(value=Config.DEFAULT_SUBREDDIT)
        subreddit_entry = ttk.Entry(subreddit_input_frame, textvariable=self.subreddit_var)
        subreddit_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(subreddit_input_frame, text="Info", command=self.show_subreddit_info).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Flair
        ttk.Label(details_frame, text="Flair (optional):").pack(anchor=tk.W)
        self.flair_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.flair_var, width=50).pack(fill=tk.X, pady=(0, 10))
        
        # Description
        ttk.Label(details_frame, text="Description (optional):").pack(anchor=tk.W)
        self.description_text = scrolledtext.ScrolledText(details_frame, height=6, width=50)
        self.description_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Post Image", command=self.post_image_async,
                  style="Accent.TButton").pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Clear All", command=self.clear_form).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(button_frame, text="History", command=self.show_history).pack(side=tk.RIGHT)
        
        # Progress bar
        self.progress_var = tk.StringVar()
        self.progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        self.progress_label.pack(pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
    
    def browse_image(self):
        """Browse for image file"""
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.webp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("GIF files", "*.gif"),
            ("WebP files", "*.webp"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=filetypes
        )
        
        if filename:
            self.image_path_var.set(filename)
            # Auto-generate title from filename if title is empty
            if not self.title_var.get():
                title = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
                self.title_var.set(title)
    
    def show_subreddit_info(self):
        """Show subreddit information"""
        if not self.bot:
            messagebox.showerror("Error", "Bot not connected")
            return
        
        subreddit = self.subreddit_var.get().strip()
        if not subreddit:
            messagebox.showwarning("Warning", "Please enter a subreddit name")
            return
        
        try:
            info = self.bot.get_subreddit_info(subreddit)
            
            info_text = f"""
Subreddit: r/{info['name']}
Title: {info['title']}
Subscribers: {info['subscribers']:,}
Rules: {info['rules_count']}
Allows Images: {'Yes' if info['allow_images'] else 'No'}

Description:
{info['description']}
            """.strip()
            
            messagebox.showinfo(f"r/{info['name']} Info", info_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not get subreddit info:\n{e}")
    
    def clear_form(self):
        """Clear all form fields"""
        self.image_path_var.set("")
        self.title_var.set("")
        self.subreddit_var.set(Config.DEFAULT_SUBREDDIT)
        self.flair_var.set("")
        self.description_text.delete(1.0, tk.END)
        self.progress_var.set("")
    
    def post_image_async(self):
        """Post image in a separate thread"""
        if not self.validate_form():
            return
        
        # Start progress bar
        self.progress_bar.start()
        self.progress_var.set("Posting image...")
        
        # Disable the post button
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "Post Image" in str(child['text']):
                        child.configure(state='disabled')
        
        # Start posting in thread
        thread = threading.Thread(target=self.post_image_worker)
        thread.daemon = True
        thread.start()
    
    def validate_form(self):
        """Validate form inputs"""
        if not self.bot:
            messagebox.showerror("Error", "Bot not connected")
            return False
        
        if not self.image_path_var.get():
            messagebox.showwarning("Warning", "Please select an image")
            return False
        
        if not self.title_var.get().strip():
            messagebox.showwarning("Warning", "Please enter a title")
            return False
        
        if not self.subreddit_var.get().strip():
            messagebox.showwarning("Warning", "Please enter a subreddit")
            return False
        
        return True
    
    def post_image_worker(self):
        """Worker thread for posting image"""
        try:
            # Get form data
            image_path = self.image_path_var.get()
            title = self.title_var.get().strip()
            subreddit = self.subreddit_var.get().strip()
            description = self.description_text.get(1.0, tk.END).strip()
            flair = self.flair_var.get().strip()
            
            # Post the image
            post_url = self.bot.post_image(
                image_path=image_path,
                title=title,
                subreddit_name=subreddit,
                description=description if description else "",
                flair_text=flair if flair else None
            )
            
            # Update UI in main thread
            self.root.after(0, self.post_success, post_url)
            
        except Exception as e:
            # Update UI in main thread
            self.root.after(0, self.post_error, str(e))
    
    def post_success(self, post_url):
        """Handle successful post"""
        self.progress_bar.stop()
        self.progress_var.set("Posted successfully!")
        
        # Re-enable post button
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "Post Image" in str(child['text']):
                        child.configure(state='normal')
        
        # Show success dialog
        result = messagebox.askquestion(
            "Success!",
            f"Image posted successfully!\n\nWould you like to open the post in your browser?",
            icon='question'
        )
        
        if result == 'yes':
            webbrowser.open(post_url)
        
        # Clear form
        self.clear_form()
    
    def post_error(self, error_message):
        """Handle post error"""
        self.progress_bar.stop()
        self.progress_var.set("Post failed")
        
        # Re-enable post button
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button) and "Post Image" in str(child['text']):
                        child.configure(state='normal')
        
        messagebox.showerror("Post Failed", f"Failed to post image:\n\n{error_message}")
    
    def show_history(self):
        """Show user's post history"""
        if not self.bot:
            messagebox.showerror("Error", "Bot not connected")
            return
        
        try:
            posts = self.bot.list_user_posts(limit=10)
            
            if not posts:
                messagebox.showinfo("History", "No recent posts found")
                return
            
            # Create history window
            history_window = tk.Toplevel(self.root)
            history_window.title("Post History")
            history_window.geometry("600x400")
            
            # Create treeview for posts
            columns = ('Title', 'Subreddit', 'Score')
            tree = ttk.Treeview(history_window, columns=columns, show='headings')
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Add posts to tree
            for post in posts:
                tree.insert('', tk.END, values=(
                    post['title'][:50] + '...' if len(post['title']) > 50 else post['title'],
                    f"r/{post['subreddit']}",
                    post['score']
                ))
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack widgets
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind double-click to open post
            def on_double_click(event):
                item = tree.selection()[0]
                post_index = tree.index(item)
                webbrowser.open(posts[post_index]['url'])
            
            tree.bind('<Double-1>', on_double_click)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load history:\n{e}")
    
    def load_settings(self):
        """Load any saved settings"""
        # This could be expanded to load settings from a file
        pass

def main():
    """Main entry point for GUI"""
    try:
        Config.validate()
    except ValueError as e:
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showerror(
            "Configuration Error",
            f"Reddit API credentials not found:\n{e}\n\n" +
            "Please create a .env file with your Reddit API credentials.\n" +
            "See env_example.txt for the required format.\n\n" +
            "Get credentials at: https://www.reddit.com/prefs/apps"
        )
        return
    
    root = tk.Tk()
    app = RedditBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
