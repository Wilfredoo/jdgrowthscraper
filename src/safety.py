import time
import json
import logging
from typing import Set, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

class SafetyManager:
    """Manages safety features to prevent spam and account restrictions."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_file = Path('logs/safety_data.json')
        self.data_file.parent.mkdir(exist_ok=True)
        
        # Load existing data
        self.data = self._load_safety_data()
        
        # Rate limiting counters
        self.comments_today = self.data.get('comments_today', 0)
        self.last_reset_date = self.data.get('last_reset_date', str(datetime.now().date()))
        self.commented_posts = set(self.data.get('commented_posts', []))
        self.error_count = 0
        
        # Safety limits
        self.MAX_COMMENTS_PER_DAY = 50
        self.MAX_COMMENTS_PER_HOUR = 10
        self.MAX_CONSECUTIVE_ERRORS = 5
        self.MIN_DELAY_BETWEEN_COMMENTS = 30  # seconds
        
        self.hourly_comments = []
        self.last_comment_time = None
    
    def _load_safety_data(self) -> Dict[str, Any]:
        """Load safety data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load safety data: {str(e)}")
        
        return {}
    
    def _save_safety_data(self):
        """Save safety data to file."""
        try:
            data_to_save = {
                'comments_today': self.comments_today,
                'last_reset_date': self.last_reset_date,
                'commented_posts': list(self.commented_posts),
                'last_updated': str(datetime.now())
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Could not save safety data: {str(e)}")
    
    def reset_daily_counters_if_needed(self):
        """Reset daily counters if it's a new day."""
        today = str(datetime.now().date())
        
        if self.last_reset_date != today:
            self.logger.info("New day detected - resetting daily counters")
            self.comments_today = 0
            self.last_reset_date = today
            self.error_count = 0
            self._save_safety_data()
    
    def can_comment(self, post_id: str) -> tuple[bool, str]:
        """Check if it's safe to comment on a post."""
        self.reset_daily_counters_if_needed()
        
        # Check if already commented on this post
        if post_id in self.commented_posts:
            return False, "Already commented on this post"
        
        # Check daily limit
        if self.comments_today >= self.MAX_COMMENTS_PER_DAY:
            return False, f"Daily comment limit reached ({self.MAX_COMMENTS_PER_DAY})"
        
        # Check hourly limit
        self._cleanup_hourly_comments()
        if len(self.hourly_comments) >= self.MAX_COMMENTS_PER_HOUR:
            return False, f"Hourly comment limit reached ({self.MAX_COMMENTS_PER_HOUR})"
        
        # Check time since last comment
        if self.last_comment_time:
            time_since_last = time.time() - self.last_comment_time
            if time_since_last < self.MIN_DELAY_BETWEEN_COMMENTS:
                remaining = self.MIN_DELAY_BETWEEN_COMMENTS - time_since_last
                return False, f"Must wait {remaining:.1f}s before next comment"
        
        # Check error count
        if self.error_count >= self.MAX_CONSECUTIVE_ERRORS:
            return False, f"Too many consecutive errors ({self.error_count})"
        
        return True, "Safe to comment"
    
    def record_comment(self, post_id: str, success: bool):
        """Record a comment attempt."""
        current_time = time.time()
        
        if success:
            self.comments_today += 1
            self.commented_posts.add(post_id)
            self.hourly_comments.append(current_time)
            self.last_comment_time = current_time
            self.error_count = 0  # Reset error count on success
            
            self.logger.info(f"Comment recorded - Daily: {self.comments_today}/{self.MAX_COMMENTS_PER_DAY}, Hourly: {len(self.hourly_comments)}/{self.MAX_COMMENTS_PER_HOUR}")
        else:
            self.error_count += 1
            self.logger.warning(f"Comment failed - Error count: {self.error_count}")
        
        self._save_safety_data()
    
    def _cleanup_hourly_comments(self):
        """Remove comments older than 1 hour from hourly tracking."""
        one_hour_ago = time.time() - 3600
        self.hourly_comments = [t for t in self.hourly_comments if t > one_hour_ago]
    
    def get_recommended_delay(self) -> float:
        """Get recommended delay before next action."""
        base_delay = self.config.delay_between_comments
        
        # Increase delay based on recent activity
        recent_comments = len(self.hourly_comments)
        if recent_comments > 5:
            multiplier = 1.5
        elif recent_comments > 8:
            multiplier = 2.0
        else:
            multiplier = 1.0
        
        # Add random variation
        import random
        variation = random.uniform(0.8, 1.2)
        
        return base_delay * multiplier * variation
    
    def should_take_break(self) -> tuple[bool, str]:
        """Determine if we should take a longer break."""
        
        # Take break if approaching daily limit
        if self.comments_today >= self.MAX_COMMENTS_PER_DAY * 0.8:
            return True, "Approaching daily comment limit"
        
        # Take break if too many recent comments
        if len(self.hourly_comments) >= self.MAX_COMMENTS_PER_HOUR * 0.8:
            return True, "High activity in past hour"
        
        # Take break if consecutive errors
        if self.error_count >= 3:
            return True, f"Multiple consecutive errors ({self.error_count})"
        
        return False, "No break needed"
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get current safety status."""
        self.reset_daily_counters_if_needed()
        self._cleanup_hourly_comments()
        
        return {
            'comments_today': self.comments_today,
            'daily_limit': self.MAX_COMMENTS_PER_DAY,
            'comments_this_hour': len(self.hourly_comments),
            'hourly_limit': self.MAX_COMMENTS_PER_HOUR,
            'error_count': self.error_count,
            'max_errors': self.MAX_CONSECUTIVE_ERRORS,
            'total_commented_posts': len(self.commented_posts),
            'last_comment_time': datetime.fromtimestamp(self.last_comment_time).isoformat() if self.last_comment_time else None
        }

class ErrorHandler:
    """Handles errors and implements retry logic."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.retry_delays = [5, 10, 20, 30, 60]  # Progressive delays
    
    def handle_error(self, error: Exception, context: str, attempt: int = 1) -> bool:
        """Handle an error and determine if we should retry."""
        
        error_msg = str(error).lower()
        
        # Critical errors that should stop execution
        critical_errors = [
            'invalid session',
            'account suspended',
            'rate limit exceeded',
            'blocked',
            'login required'
        ]
        
        for critical in critical_errors:
            if critical in error_msg:
                self.logger.error(f"Critical error in {context}: {error}")
                return False
        
        # Temporary errors that can be retried
        if attempt <= len(self.retry_delays):
            delay = self.retry_delays[attempt - 1]
            self.logger.warning(f"Temporary error in {context} (attempt {attempt}): {error}. Retrying in {delay}s...")
            time.sleep(delay)
            return True
        
        self.logger.error(f"Max retries exceeded for {context}: {error}")
        return False
    
    def is_temporary_error(self, error: Exception) -> bool:
        """Check if an error is likely temporary."""
        error_msg = str(error).lower()
        
        temporary_indicators = [
            'timeout',
            'connection',
            'network',
            'temporary',
            'try again',
            'server error',
            'stale element'
        ]
        
        return any(indicator in error_msg for indicator in temporary_indicators)