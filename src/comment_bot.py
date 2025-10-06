import time
import random
import logging
from typing import List, Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class CommentBot:
    """Handles automated commenting on Facebook posts."""
    
    def __init__(self, browser, config):
        self.browser = browser
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.commented_posts = set()  # Track posts we've commented on
    
    def comment_on_posts(self, posts: List[Any]) -> Dict[str, Any]:
        """Comment on a list of posts."""
        results = {
            'total_posts': len(posts),
            'successful_comments': 0,
            'failed_comments': 0,
            'skipped_posts': 0,
            'errors': []
        }
        
        self.logger.info(f"Starting to comment on {len(posts)} posts...")
        
        for i, post in enumerate(posts):
            try:
                # Skip if already commented
                if post.has_commented or post.post_id in self.commented_posts:
                    self.logger.info(f"Skipping post {i+1} - already commented")
                    results['skipped_posts'] += 1
                    continue
                
                self.logger.info(f"Commenting on post {i+1}/{len(posts)} by {post.author_name}")
                
                # Scroll to post to make it visible
                self._scroll_to_element(post.element)
                time.sleep(random.uniform(1, 2))
                
                # Add comment
                if self._add_comment_to_post(post):
                    results['successful_comments'] += 1
                    self.commented_posts.add(post.post_id)
                    self.logger.info(f"Successfully commented on post by {post.author_name}")
                else:
                    results['failed_comments'] += 1
                    self.logger.warning(f"Failed to comment on post by {post.author_name}")
                
                # Wait between comments to avoid being flagged
                delay = random.uniform(
                    self.config.delay_between_comments * 0.8,
                    self.config.delay_between_comments * 1.2
                )
                self.logger.info(f"Waiting {delay:.1f}s before next comment...")
                time.sleep(delay)
                
            except Exception as e:
                error_msg = f"Error commenting on post {i+1}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['failed_comments'] += 1
                
                # Short delay before continuing
                time.sleep(random.uniform(2, 4))
        
        self.logger.info(f"Commenting completed: {results['successful_comments']} successful, {results['failed_comments']} failed, {results['skipped_posts']} skipped")
        return results
    
    def _scroll_to_element(self, element):
        """Scroll to make an element visible."""
        try:
            self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(random.uniform(0.5, 1))
        except Exception as e:
            self.logger.debug(f"Error scrolling to element: {str(e)}")
    
    def _add_comment_to_post(self, post) -> bool:
        """Add a comment to a specific post."""
        try:
            # Get random message
            message = random.choice(self.config.admin_messages)
            
            # Try to find comment box
            comment_box = self._find_comment_box(post.element)
            if not comment_box:
                self.logger.warning("Could not find comment box")
                return False
            
            # Click on comment box to activate it
            self._click_element_safely(comment_box)
            time.sleep(random.uniform(1, 2))
            
            # Type the message with human-like delays
            self._type_message_humanlike(comment_box, message)
            time.sleep(random.uniform(1, 2))
            
            # Find and click submit button
            if self._submit_comment(post.element):
                time.sleep(random.uniform(2, 3))
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding comment: {str(e)}")
            return False
    
    def _find_comment_box(self, post_element):
        """Find the comment input box for a post."""
        try:
            # Multiple selectors to try for comment boxes
            comment_selectors = [
                "div[contenteditable='true'][data-testid='ufi_comment_textinput']",
                "div[contenteditable='true'][role='textbox']",
                "textarea[placeholder*='comment']",
                "textarea[placeholder*='Write']",
                "div[data-testid='ufi_comment_textinput']",
                "[contenteditable='true'][aria-label*='comment']",
                "[contenteditable='true'][aria-label*='Write']",
                "div[role='textbox']",
                ".UFIAddComment textarea",
                ".UFIAddComment div[contenteditable='true']"
            ]
            
            for selector in comment_selectors:
                try:
                    comment_boxes = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for box in comment_boxes:
                        if box.is_displayed() and box.is_enabled():
                            return box
                except:
                    continue
            
            # Try to find "Write a comment" or similar text and click it
            comment_triggers = [
                "Write a comment",
                "Add a comment",
                "Comment",
                "Write something"
            ]
            
            for trigger_text in comment_triggers:
                try:
                    trigger_elements = post_element.find_elements(By.XPATH, f".//*[contains(text(), '{trigger_text}')]")
                    for trigger in trigger_elements:
                        if trigger.is_displayed():
                            trigger.click()
                            time.sleep(1)
                            # Try to find comment box again
                            for selector in comment_selectors[:3]:
                                try:
                                    comment_box = post_element.find_element(By.CSS_SELECTOR, selector)
                                    if comment_box.is_displayed():
                                        return comment_box
                                except:
                                    continue
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error finding comment box: {str(e)}")
            return None
    
    def _click_element_safely(self, element):
        """Safely click an element with retries."""
        try:
            # Try regular click first
            element.click()
        except Exception:
            try:
                # Try JavaScript click
                self.browser.driver.execute_script("arguments[0].click();", element)
            except Exception:
                try:
                    # Try ActionChains click
                    ActionChains(self.browser.driver).move_to_element(element).click().perform()
                except Exception as e:
                    self.logger.debug(f"All click methods failed: {str(e)}")
    
    def _type_message_humanlike(self, element, message):
        """Type message with human-like delays and patterns."""
        try:
            # Clear existing content
            element.clear()
            
            # Type character by character with random delays
            for char in message:
                element.send_keys(char)
                
                # Random delay between characters (simulate human typing)
                if char == ' ':
                    time.sleep(random.uniform(0.1, 0.3))  # Longer pause after words
                else:
                    time.sleep(random.uniform(0.05, 0.15))  # Regular typing speed
                
                # Occasional longer pauses (simulate thinking)
                if random.random() < 0.1:  # 10% chance
                    time.sleep(random.uniform(0.3, 0.8))
            
        except Exception as e:
            # Fallback: send all text at once
            try:
                element.clear()
                element.send_keys(message)
            except Exception as e2:
                self.logger.error(f"Failed to type message: {str(e2)}")
    
    def _submit_comment(self, post_element) -> bool:
        """Submit the comment."""
        try:
            # Multiple selectors for submit buttons
            submit_selectors = [
                "button[type='submit']",
                "button[data-testid='ufi_comment_submit']",
                "[aria-label='Post']",
                "[aria-label='Comment']",
                ".UFICommentSubmit",
                "button[value='1'][name='post']",
                "input[type='submit'][value='Comment']"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_buttons = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for button in submit_buttons:
                        if button.is_displayed() and button.is_enabled():
                            self._click_element_safely(button)
                            return True
                except:
                    continue
            
            # Try pressing Enter as fallback
            try:
                comment_box = self._find_comment_box(post_element)
                if comment_box:
                    comment_box.send_keys(Keys.RETURN)
                    return True
            except:
                pass
            
            self.logger.warning("Could not find submit button")
            return False
            
        except Exception as e:
            self.logger.error(f"Error submitting comment: {str(e)}")
            return False
    
    def verify_comment_posted(self, post_element, message: str) -> bool:
        """Verify that a comment was successfully posted."""
        try:
            # Wait a moment for comment to appear
            time.sleep(3)
            
            # Look for the comment in the post
            comment_elements = post_element.find_elements(By.CSS_SELECTOR, ".UFIComment, [data-testid='UFI2Comment/root']")
            
            for comment in comment_elements:
                if message.lower() in comment.text.lower():
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error verifying comment: {str(e)}")
            return False