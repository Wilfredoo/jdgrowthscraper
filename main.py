#!/usr/bin/env python3
"""
JD Growth Scraper - Facebook Group Automation Tool
Automates admin commenting on Facebook group posts.
"""

import sys
import time
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from config import Config
from browser import FacebookBrowser
from scraper import PostScraper
from comment_bot import CommentBot
from safety import SafetyManager, ErrorHandler

class JDGrowthScraper:
    """Main application class for the Facebook group scraper."""
    
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.safety_manager = SafetyManager(self.config)
        self.error_handler = ErrorHandler(self.config)
        
    def run(self):
        """Main execution method."""
        try:
            # Validate configuration
            if not self.config.validate():
                self.logger.error("Configuration validation failed. Please check your .env file.")
                return False
            
            # Display safety status
            status = self.safety_manager.get_status_report()
            self.logger.info("=== Safety Status ===")
            self.logger.info(f"Comments today: {status['comments_today']}/{status['daily_limit']}")
            self.logger.info(f"Comments this hour: {status['comments_this_hour']}/{status['hourly_limit']}")
            self.logger.info(f"Total posts commented: {status['total_commented_posts']}")
            
            # Check if we should take a break
            should_break, break_reason = self.safety_manager.should_take_break()
            if should_break:
                self.logger.warning(f"Taking a break: {break_reason}")
                return True
            
            # Initialize browser and run scraping
            with FacebookBrowser(self.config) as browser:
                return self._run_scraping_session(browser)
                
        except KeyboardInterrupt:
            self.logger.info("Scraping interrupted by user")
            return True
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return False
    
    def _run_scraping_session(self, browser) -> bool:
        """Run a complete scraping session."""
        try:
            # Setup browser
            self.logger.info("Setting up browser...")
            if not browser.setup_driver():
                self.logger.error("Failed to setup browser driver")
                return False
            
            # Login to Facebook
            self.logger.info("Logging into Facebook...")
            if not browser.login():
                self.logger.error("Failed to login to Facebook")
                return False
            
            # Navigate to group
            self.logger.info(f"Navigating to group: {self.config.group_url}")
            if not browser.navigate_to_group():
                self.logger.error("Failed to navigate to group")
                return False
            
            # Initialize scrapers
            post_scraper = PostScraper(browser, self.config)
            comment_bot = CommentBot(browser, self.config)
            
            # Scrape posts
            self.logger.info("Scraping recent posts...")
            posts = post_scraper.get_recent_posts()
            
            if not posts:
                self.logger.warning("No posts found to process")
                return True
            
            # Filter posts based on safety rules
            safe_posts = []
            for post in posts:
                can_comment, reason = self.safety_manager.can_comment(post.post_id)
                if can_comment:
                    safe_posts.append(post)
                else:
                    self.logger.info(f"Skipping post by {post.author_name}: {reason}")
            
            if not safe_posts:
                self.logger.info("No posts available for commenting after safety checks")
                return True
            
            self.logger.info(f"Found {len(safe_posts)} posts ready for commenting")
            
            # Comment on posts
            results = self._comment_on_posts_safely(comment_bot, safe_posts)
            
            # Log results
            self._log_session_results(results)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in scraping session: {str(e)}")
            return False
    
    def _comment_on_posts_safely(self, comment_bot, posts) -> dict:
        """Comment on posts with safety checks."""
        results = {
            'total_posts': len(posts),
            'successful_comments': 0,
            'failed_comments': 0,
            'skipped_posts': 0,
            'safety_stops': 0
        }
        
        for i, post in enumerate(posts):
            try:
                # Final safety check before commenting
                can_comment, reason = self.safety_manager.can_comment(post.post_id)
                if not can_comment:
                    self.logger.info(f"Safety check failed for post {i+1}: {reason}")
                    results['skipped_posts'] += 1
                    continue
                
                self.logger.info(f"Commenting on post {i+1}/{len(posts)} by {post.author_name}")
                
                # Attempt to comment
                success = self._attempt_comment_with_retry(comment_bot, post)
                
                # Record the attempt
                self.safety_manager.record_comment(post.post_id, success)
                
                if success:
                    results['successful_comments'] += 1
                    self.logger.info(f"✓ Successfully commented on post by {post.author_name}")
                else:
                    results['failed_comments'] += 1
                    self.logger.warning(f"✗ Failed to comment on post by {post.author_name}")
                
                # Check if we should stop for safety
                should_break, break_reason = self.safety_manager.should_take_break()
                if should_break:
                    self.logger.info(f"Stopping session for safety: {break_reason}")
                    results['safety_stops'] += 1
                    break
                
                # Wait before next comment
                delay = self.safety_manager.get_recommended_delay()
                self.logger.info(f"Waiting {delay:.1f}s before next comment...")
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Error processing post {i+1}: {str(e)}")
                results['failed_comments'] += 1
                
                # Short delay before continuing
                time.sleep(5)
        
        return results
    
    def _attempt_comment_with_retry(self, comment_bot, post, max_attempts=3) -> bool:
        """Attempt to comment with retry logic."""
        for attempt in range(1, max_attempts + 1):
            try:
                # Create a single-post list for the comment_bot method
                single_post_results = comment_bot.comment_on_posts([post])
                return single_post_results['successful_comments'] > 0
                
            except Exception as e:
                if self.error_handler.handle_error(e, f"commenting on post", attempt):
                    continue  # Retry
                else:
                    return False  # Give up
        
        return False
    
    def _log_session_results(self, results):
        """Log the results of the scraping session."""
        self.logger.info("=== Session Results ===")
        self.logger.info(f"Total posts processed: {results['total_posts']}")
        self.logger.info(f"Successful comments: {results['successful_comments']}")
        self.logger.info(f"Failed comments: {results['failed_comments']}")
        self.logger.info(f"Skipped posts: {results['skipped_posts']}")
        
        if results.get('safety_stops', 0) > 0:
            self.logger.info(f"Safety stops: {results['safety_stops']}")
        
        # Update safety status
        status = self.safety_manager.get_status_report()
        self.logger.info(f"Updated daily count: {status['comments_today']}/{status['daily_limit']}")

def main():
    """Main entry point."""
    print("🚀 JD Growth Scraper Starting...")
    print("📋 Facebook Group Automation Tool")
    print("=" * 50)
    
    scraper = JDGrowthScraper()
    
    try:
        success = scraper.run()
        if success:
            print("\n✅ Scraping session completed successfully!")
        else:
            print("\n❌ Scraping session failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()