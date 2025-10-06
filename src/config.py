import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

class Config:
    """Configuration manager for the Facebook scraper."""
    
    def __init__(self):
        load_dotenv()
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    @property
    def facebook_email(self) -> str:
        return os.getenv('FACEBOOK_EMAIL', '')
    
    @property
    def facebook_password(self) -> str:
        return os.getenv('FACEBOOK_PASSWORD', '')
    
    @property
    def group_id(self) -> str:
        return os.getenv('GROUP_ID', '426796887732920')
    
    @property
    def group_url(self) -> str:
        return os.getenv('GROUP_URL', f'https://www.facebook.com/groups/{self.group_id}')
    
    @property
    def max_posts_to_process(self) -> int:
        return int(os.getenv('MAX_POSTS_TO_PROCESS', '10'))
    
    @property
    def delay_between_actions(self) -> int:
        return int(os.getenv('DELAY_BETWEEN_ACTIONS', '3'))
    
    @property
    def delay_between_comments(self) -> int:
        return int(os.getenv('DELAY_BETWEEN_COMMENTS', '30'))
    
    @property
    def admin_messages(self) -> List[str]:
        messages = os.getenv('ADMIN_MESSAGES', 'Thanks for sharing this with the group!')
        return [msg.strip() for msg in messages.split(',')]
    
    @property
    def headless_mode(self) -> bool:
        return os.getenv('HEADLESS_MODE', 'False').lower() == 'true'
    
    @property
    def browser_timeout(self) -> int:
        return int(os.getenv('BROWSER_TIMEOUT', '30'))
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        if not self.facebook_email or not self.facebook_password:
            self.logger.error("Facebook credentials not provided in .env file")
            return False
        
        if not self.group_id:
            self.logger.error("Group ID not provided in .env file")
            return False
        
        return True