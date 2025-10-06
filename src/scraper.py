import time
import random
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

@dataclass
class FacebookPost:
    """Represents a Facebook post."""
    post_id: str
    author_name: str
    content: str
    timestamp: str
    element: Any  # The selenium element
    has_commented: bool = False

class PostScraper:
    """Scrapes posts from Facebook groups."""
    
    def __init__(self, browser, config):
        self.browser = browser
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processed_posts = set()  # Track processed post IDs
    
    def get_recent_posts(self, max_posts: Optional[int] = None) -> List[FacebookPost]:
        """Scrape recent posts from the group."""
        if max_posts is None:
            max_posts = self.config.max_posts_to_process
        
        self.logger.info(f"Scraping up to {max_posts} recent posts...")
        posts = []
        
        try:
            # Scroll down a bit to load more posts
            self._scroll_to_load_posts()
            
            # Find all post containers
            post_elements = self._find_post_elements()
            
            self.logger.info(f"Found {len(post_elements)} potential posts")
            
            for i, post_element in enumerate(post_elements[:max_posts]):
                try:
                    post = self._extract_post_data(post_element, i)
                    if post and post.post_id not in self.processed_posts:
                        posts.append(post)
                        self.processed_posts.add(post.post_id)
                        
                        self.logger.info(f"Extracted post {len(posts)}: {post.author_name[:30]}...")
                        
                        if len(posts) >= max_posts:
                            break
                    
                    # Small delay between processing posts
                    time.sleep(random.uniform(0.5, 1.5))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to extract post {i}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(posts)} posts")
            return posts
            
        except Exception as e:
            self.logger.error(f"Failed to scrape posts: {str(e)}")
            return []
    
    def _scroll_to_load_posts(self):
        """Scroll down to load more posts."""
        try:
            # Scroll down a few times to load more content
            for i in range(3):
                self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(random.uniform(1, 2))
                
                self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
            # Scroll back to top
            self.browser.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
        except Exception as e:
            self.logger.warning(f"Error during scrolling: {str(e)}")
    
    def _find_post_elements(self) -> List[Any]:
        """Find all post elements on the page."""
        try:
            # Multiple selectors to try for post containers
            post_selectors = [
                "div[role='article']",
                "div[data-pagelet='FeedUnit']",
                "div[data-ft]",
                "div[data-testid='fbfeed_story']",
                ".userContentWrapper",
                "[data-testid='story-subtitle']"
            ]
            
            all_posts = []
            
            for selector in post_selectors:
                try:
                    posts = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    if posts:
                        self.logger.info(f"Found {len(posts)} posts with selector: {selector}")
                        all_posts.extend(posts)
                        break  # Use the first successful selector
                except Exception as e:
                    continue
            
            # Remove duplicates while preserving order
            seen = set()
            unique_posts = []
            for post in all_posts:
                try:
                    post_id = post.get_attribute('data-ft') or post.get_attribute('id') or str(hash(post.get_attribute('outerHTML')[:100]))
                    if post_id not in seen:
                        seen.add(post_id)
                        unique_posts.append(post)
                except:
                    unique_posts.append(post)  # Include anyway if we can't get ID
            
            return unique_posts[:20]  # Limit to reasonable number
            
        except Exception as e:
            self.logger.error(f"Failed to find post elements: {str(e)}")
            return []
    
    def _extract_post_data(self, post_element, index: int) -> Optional[FacebookPost]:
        """Extract data from a single post element."""
        try:
            # Generate a unique post ID
            post_id = self._get_post_id(post_element, index)
            
            # Extract author name
            author_name = self._extract_author_name(post_element)
            
            # Extract post content
            content = self._extract_post_content(post_element)
            
            # Extract timestamp
            timestamp = self._extract_timestamp(post_element)
            
            # Check if we've already commented
            has_commented = self._check_if_commented(post_element)
            
            if not author_name or not content:
                self.logger.debug(f"Skipping post {index} - insufficient data")
                return None
            
            return FacebookPost(
                post_id=post_id,
                author_name=author_name,
                content=content,
                timestamp=timestamp,
                element=post_element,
                has_commented=has_commented
            )
            
        except Exception as e:
            self.logger.warning(f"Error extracting post data: {str(e)}")
            return None
    
    def _get_post_id(self, post_element, index: int) -> str:
        """Generate a unique ID for the post."""
        try:
            # Try various attributes that might contain unique identifiers
            for attr in ['data-ft', 'id', 'data-testid']:
                value = post_element.get_attribute(attr)
                if value:
                    return f"{attr}_{value}"
            
            # Fallback: use hash of content
            content_hash = str(hash(post_element.get_attribute('outerHTML')[:200]))
            return f"hash_{content_hash}_{index}"
            
        except:
            return f"post_{index}_{int(time.time())}"
    
    def _extract_author_name(self, post_element) -> str:
        """Extract the author's name from the post."""
        try:
            # Multiple selectors to try for author name
            author_selectors = [
                "strong a",
                "h3 a",
                "[data-testid='story-subtitle'] a",
                ".actor a",
                "a[role='link'][tabindex='0']",
                "span strong",
            ]
            
            for selector in author_selectors:
                try:
                    author_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    author_name = author_element.get_attribute('aria-label') or author_element.text
                    if author_name and len(author_name.strip()) > 0:
                        return author_name.strip()
                except:
                    continue
            
            return "Unknown Author"
            
        except Exception as e:
            self.logger.debug(f"Error extracting author name: {str(e)}")
            return "Unknown Author"
    
    def _extract_post_content(self, post_element) -> str:
        """Extract the post content/text."""
        try:
            # Multiple selectors for post content
            content_selectors = [
                "[data-testid='post_message']",
                ".userContent",
                "[data-ad-preview='message']",
                "div[data-testid='story-subtitle'] ~ div",
                "div[dir='auto']",
            ]
            
            for selector in content_selectors:
                try:
                    content_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    content = content_element.text.strip()
                    if content and len(content) > 10:  # Ensure substantial content
                        return content[:500]  # Limit length
                except:
                    continue
            
            # Fallback: get any text content
            text_content = post_element.text.strip()
            if text_content:
                return text_content[:200]
            
            return "No content found"
            
        except Exception as e:
            self.logger.debug(f"Error extracting post content: {str(e)}")
            return "No content found"
    
    def _extract_timestamp(self, post_element) -> str:
        """Extract the post timestamp."""
        try:
            # Look for timestamp elements
            timestamp_selectors = [
                "a[role='link'] abbr",
                "[data-testid='story-subtitle'] a",
                "time",
                ".timestamp",
                "abbr[data-utime]"
            ]
            
            for selector in timestamp_selectors:
                try:
                    timestamp_element = post_element.find_element(By.CSS_SELECTOR, selector)
                    timestamp = timestamp_element.get_attribute('title') or timestamp_element.text
                    if timestamp:
                        return timestamp.strip()
                except:
                    continue
            
            return "Unknown time"
            
        except Exception as e:
            self.logger.debug(f"Error extracting timestamp: {str(e)}")
            return "Unknown time"
    
    def _check_if_commented(self, post_element) -> bool:
        """Check if we've already commented on this post."""
        try:
            # Look for our own comments (this is a basic check)
            # In a real implementation, you might want to store commented post IDs
            
            # Look for comment section
            comment_selectors = [
                ".UFIComment",
                "[data-testid='UFI2Comment/root']",
                ".comment",
            ]
            
            for selector in comment_selectors:
                try:
                    comments = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for comment in comments:
                        # Check if any comment contains our admin messages
                        comment_text = comment.text.lower()
                        for message in self.config.admin_messages:
                            if message.lower() in comment_text:
                                return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking if commented: {str(e)}")
            return False