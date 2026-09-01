#!/usr/bin/env python3
"""
Enhanced Reddit Image Bot with Automation Features
Supports batch uploading, scheduling, and advanced management
"""

import os
import sys
import json
import time
import schedule
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from PIL import Image
import praw
from reddit_bot.config import Config

@dataclass
class UploadJob:
    """Represents a single upload job"""
    id: str
    image_path: str
    title: str
    subreddit: str
    description: str = ""
    flair_text: Optional[str] = None
    scheduled_time: Optional[str] = None  # ISO format
    status: str = "pending"  # pending, uploading, completed, failed
    created_at: str = ""
    completed_at: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class BatchUploadConfig:
    """Configuration for batch uploads"""
    interval_minutes: int = 5  # Time between uploads
    max_concurrent: int = 1    # Max concurrent uploads
    retry_failed: bool = True  # Retry failed uploads
    auto_schedule: bool = False # Auto-schedule based on interval

class AutomatedRedditBot:
    """Enhanced Reddit bot with automation capabilities"""
    
    def __init__(self, db_path: str = "reddit_bot.db"):
        """Initialize the automated Reddit bot"""
        self.db_path = db_path
        self.init_database()
        
        # Initialize Reddit API
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
        
        # Scheduling
        self.scheduler_running = False
        self.scheduler_thread = None
        
    def init_database(self):
        """Initialize SQLite database for job tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS upload_jobs (
                    id TEXT PRIMARY KEY,
                    image_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    subreddit TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    flair_text TEXT,
                    scheduled_time TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    post_url TEXT,
                    error_message TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS batch_configs (
                    id INTEGER PRIMARY KEY,
                    config_name TEXT UNIQUE,
                    interval_minutes INTEGER,
                    max_concurrent INTEGER,
                    retry_failed INTEGER,
                    auto_schedule INTEGER,
                    created_at TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS upload_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    action TEXT,
                    timestamp TEXT,
                    details TEXT
                )
            ''')
            conn.commit()
    
    def add_upload_job(self, job: UploadJob) -> str:
        """Add an upload job to the queue"""
        if not job.id:
            job.id = f"job_{int(time.time())}_{hash(job.image_path) % 10000}"
        
        if not job.created_at:
            job.created_at = datetime.now().isoformat()
        
        # Validate image exists
        if not os.path.exists(job.image_path):
            raise FileNotFoundError(f"Image file not found: {job.image_path}")
        
        # Validate image
        self.validate_image(job.image_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO upload_jobs 
                (id, image_path, title, subreddit, description, flair_text, 
                 scheduled_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.id, job.image_path, job.title, job.subreddit,
                job.description, job.flair_text, job.scheduled_time,
                job.status, job.created_at
            ))
            conn.commit()
        
        self.log_action(job.id, "job_created", f"Job created for {job.image_path}")
        return job.id
    
    def get_jobs(self, status: Optional[str] = None) -> List[UploadJob]:
        """Get upload jobs, optionally filtered by status"""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                cursor = conn.execute(
                    'SELECT * FROM upload_jobs WHERE status = ? ORDER BY created_at',
                    (status,)
                )
            else:
                cursor = conn.execute(
                    'SELECT * FROM upload_jobs ORDER BY created_at'
                )
            
            jobs = []
            for row in cursor.fetchall():
                job = UploadJob(
                    id=row[0], image_path=row[1], title=row[2], subreddit=row[3],
                    description=row[4], flair_text=row[5], scheduled_time=row[6],
                    status=row[7], created_at=row[8], completed_at=row[9],
                    post_url=row[10], error_message=row[11]
                )
                jobs.append(job)
            
            return jobs
    
    def update_job_status(self, job_id: str, status: str, 
                         post_url: Optional[str] = None, 
                         error_message: Optional[str] = None):
        """Update job status"""
        completed_at = datetime.now().isoformat() if status in ['completed', 'failed'] else None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE upload_jobs 
                SET status = ?, completed_at = ?, post_url = ?, error_message = ?
                WHERE id = ?
            ''', (status, completed_at, post_url, error_message, job_id))
            conn.commit()
        
        self.log_action(job_id, "status_changed", f"Status changed to {status}")
    
    def batch_upload_from_folder(self, folder_path: str, subreddit: str, 
                                config: BatchUploadConfig) -> List[str]:
        """Create batch upload jobs from a folder"""
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Find all image files
        image_files = []
        for ext in Config.SUPPORTED_FORMATS:
            image_files.extend(folder.glob(f"*{ext}"))
            image_files.extend(folder.glob(f"*{ext.upper()}"))
        
        if not image_files:
            raise ValueError(f"No supported image files found in {folder_path}")
        
        job_ids = []
        current_time = datetime.now()
        
        for i, image_file in enumerate(image_files):
            # Generate title from filename
            title = image_file.stem.replace('_', ' ').replace('-', ' ').title()
            
            # Calculate scheduled time if auto-scheduling
            scheduled_time = None
            if config.auto_schedule:
                schedule_time = current_time + timedelta(minutes=i * config.interval_minutes)
                scheduled_time = schedule_time.isoformat()
            
            job = UploadJob(
                id="",  # Will be auto-generated
                image_path=str(image_file),
                title=title,
                subreddit=subreddit,
                scheduled_time=scheduled_time
            )
            
            job_id = self.add_upload_job(job)
            job_ids.append(job_id)
        
        # Save batch config
        self.save_batch_config(f"batch_{int(time.time())}", config)
        
        print(f"Created {len(job_ids)} upload jobs from {folder_path}")
        return job_ids
    
    def process_upload_job(self, job: UploadJob) -> bool:
        """Process a single upload job"""
        try:
            print(f"Processing job {job.id}: {job.title}")
            self.update_job_status(job.id, "uploading")
            
            # Upload the image
            post_url = self.upload_image(
                image_path=job.image_path,
                title=job.title,
                subreddit_name=job.subreddit,
                description=job.description,
                flair_text=job.flair_text
            )
            
            self.update_job_status(job.id, "completed", post_url=post_url)
            print(f"Job {job.id} completed: {post_url}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.update_job_status(job.id, "failed", error_message=error_msg)
            print(f"Job {job.id} failed: {error_msg}")
            return False
    
    def start_scheduler(self):
        """Start the job scheduler"""
        if self.scheduler_running:
            print("Scheduler already running")
            return
        
        def scheduler_worker():
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        
        # Schedule job processing
        schedule.every(1).minutes.do(self.process_pending_jobs)
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
        self.scheduler_thread.start()
        print("Scheduler started")
    
    def stop_scheduler(self):
        """Stop the job scheduler"""
        self.scheduler_running = False
        schedule.clear()
        print("Scheduler stopped")
    
    def process_pending_jobs(self):
        """Process jobs that are ready to be uploaded"""
        pending_jobs = self.get_jobs("pending")
        current_time = datetime.now()
        
        for job in pending_jobs:
            # Check if job is scheduled and ready
            if job.scheduled_time:
                scheduled_dt = datetime.fromisoformat(job.scheduled_time)
                if scheduled_dt > current_time:
                    continue  # Not ready yet
            
            # Process the job
            self.process_upload_job(job)
            
            # Add delay between uploads to respect rate limits
            time.sleep(30)  # 30 seconds between uploads
    
    def upload_image(self, image_path: str, title: str, subreddit_name: str,
                    description: str = "", flair_text: Optional[str] = None) -> str:
        """Upload a single image (enhanced version of original method)"""
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
                try:
                    comment.mod.distinguish(how='yes', sticky=True)
                    print("Description comment pinned")
                except:
                    print("Description comment added (couldn't pin)")
            
            # Add flair if provided
            if flair_text:
                try:
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
                        print(f"Flair '{flair_text}' not found")
                        
                except Exception as e:
                    print(f"Could not apply flair: {e}")
            
            post_url = f"https://reddit.com{submission.permalink}"
            return post_url
            
        except Exception as e:
            print(f"Failed to upload image: {e}")
            raise
    
    def validate_image(self, image_path: str) -> bool:
        """Validate image file"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in Config.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {file_ext}")
        
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if file_size_mb > Config.MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB")
        
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")
        
        return True
    
    def validate_subreddit(self, subreddit_name: str):
        """Validate subreddit exists and is accessible"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            _ = subreddit.display_name
            return subreddit
        except Exception as e:
            raise ValueError(f"Cannot access subreddit '{subreddit_name}': {e}")
    
    def save_batch_config(self, name: str, config: BatchUploadConfig):
        """Save batch configuration"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO batch_configs 
                (config_name, interval_minutes, max_concurrent, retry_failed, 
                 auto_schedule, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                name, config.interval_minutes, config.max_concurrent,
                int(config.retry_failed), int(config.auto_schedule),
                datetime.now().isoformat()
            ))
            conn.commit()
    
    def get_batch_configs(self) -> List[Dict[str, Any]]:
        """Get saved batch configurations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM batch_configs ORDER BY created_at DESC')
            configs = []
            for row in cursor.fetchall():
                config = {
                    'id': row[0],
                    'name': row[1],
                    'interval_minutes': row[2],
                    'max_concurrent': row[3],
                    'retry_failed': bool(row[4]),
                    'auto_schedule': bool(row[5]),
                    'created_at': row[6]
                }
                configs.append(config)
            return configs
    
    def log_action(self, job_id: str, action: str, details: str):
        """Log an action to the history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO upload_history (job_id, action, timestamp, details)
                VALUES (?, ?, ?, ?)
            ''', (job_id, action, datetime.now().isoformat(), details))
            conn.commit()
    
    def get_upload_history(self, job_id: Optional[str] = None, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get upload history"""
        with sqlite3.connect(self.db_path) as conn:
            if job_id:
                cursor = conn.execute('''
                    SELECT * FROM upload_history 
                    WHERE job_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (job_id, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM upload_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            history = []
            for row in cursor.fetchall():
                entry = {
                    'id': row[0],
                    'job_id': row[1],
                    'action': row[2],
                    'timestamp': row[3],
                    'details': row[4]
                }
                history.append(entry)
            
            return history
    
    def get_stats(self) -> Dict[str, Any]:
        """Get upload statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Job counts by status
            cursor = conn.execute('SELECT status, COUNT(*) FROM upload_jobs GROUP BY status')
            stats['job_counts'] = dict(cursor.fetchall())
            
            # Total jobs
            cursor = conn.execute('SELECT COUNT(*) FROM upload_jobs')
            stats['total_jobs'] = cursor.fetchone()[0]
            
            # Recent activity (last 24 hours)
            yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor = conn.execute(
                'SELECT COUNT(*) FROM upload_jobs WHERE created_at > ?',
                (yesterday,)
            )
            stats['recent_jobs'] = cursor.fetchone()[0]
            
            # Success rate
            cursor = conn.execute('SELECT COUNT(*) FROM upload_jobs WHERE status = "completed"')
            completed = cursor.fetchone()[0]
            
            cursor = conn.execute('SELECT COUNT(*) FROM upload_jobs WHERE status IN ("completed", "failed")')
            total_processed = cursor.fetchone()[0]
            
            stats['success_rate'] = (completed / total_processed * 100) if total_processed > 0 else 0
            
            return stats

def main():
    """Main function for testing automation features"""
    bot = AutomatedRedditBot()
    
    print("Automated Reddit Bot - Test Mode")
    print("=" * 50)
    
    # Example usage
    print("\nCurrent Stats:")
    stats = bot.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print(f"\nPending Jobs: {len(bot.get_jobs('pending'))}")
    print(f"Completed Jobs: {len(bot.get_jobs('completed'))}")
    print(f"Failed Jobs: {len(bot.get_jobs('failed'))}")

if __name__ == "__main__":
    main()
