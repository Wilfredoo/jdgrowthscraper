import time
import random
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

class FacebookBrowser:
    """Handles browser automation for Facebook interactions."""
    
    def __init__(self, config):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.logger = logging.getLogger(__name__)
        self.is_logged_in = False
    
    def setup_driver(self) -> bool:
        """Initialize and configure the Chrome driver."""
        try:
            chrome_options = Options()
            
            # User agent rotation
            ua = UserAgent()
            chrome_options.add_argument(f'--user-agent={ua.chrome}')
            
            # Privacy and security options
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Headless mode
            if self.config.headless_mode:
                chrome_options.add_argument('--headless')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Set up the driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set up wait
            self.wait = WebDriverWait(self.driver, self.config.browser_timeout)
            
            self.logger.info("Browser driver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser driver: {str(e)}")
            return False
    
    def login(self) -> bool:
        """Log into Facebook."""
        try:
            self.logger.info("Attempting to log into Facebook...")
            
            # Navigate to Facebook
            self.driver.get("https://www.facebook.com")
            time.sleep(random.uniform(2, 4))
            
            # Handle cookie consent if present
            try:
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]"))
                )
                cookie_button.click()
                time.sleep(1)
            except TimeoutException:
                pass  # No cookie consent dialog
            
            # Find and fill email field
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self.config.facebook_email)
            time.sleep(random.uniform(1, 2))
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "pass")
            password_field.clear()
            password_field.send_keys(self.config.facebook_password)
            time.sleep(random.uniform(1, 2))
            
            # Click login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if self._check_login_success():
                self.is_logged_in = True
                self.logger.info("Successfully logged into Facebook")
                return True
            else:
                self.logger.error("Login failed - check credentials")
                return False
                
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            return False
    
    def _check_login_success(self) -> bool:
        """Check if login was successful."""
        try:
            # Look for elements that indicate successful login
            success_indicators = [
                (By.XPATH, "//div[@role='banner']"),  # Main navigation
                (By.XPATH, "//div[contains(@aria-label, 'Facebook')]"),  # Facebook logo
                (By.XPATH, "//a[@aria-label='Home']"),  # Home link
            ]
            
            for by, selector in success_indicators:
                try:
                    self.wait.until(EC.presence_of_element_located((by, selector)))
                    return True
                except TimeoutException:
                    continue
            
            # Check for login error messages
            error_indicators = [
                "incorrect",
                "wrong",
                "error",
                "try again"
            ]
            
            page_text = self.driver.page_source.lower()
            for error in error_indicators:
                if error in page_text:
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False
    
    def navigate_to_group(self) -> bool:
        """Navigate to the specified Facebook group."""
        try:
            self.logger.info(f"Navigating to group: {self.config.group_url}")
            
            self.driver.get(self.config.group_url)
            time.sleep(random.uniform(3, 5))
            
            # Wait for group page to load
            group_indicators = [
                (By.XPATH, "//h1[contains(@class, 'x1heor9g')]"),  # Group name
                (By.XPATH, "//div[contains(text(), 'members')]"),  # Member count
                (By.XPATH, "//span[contains(text(), 'Write something')]"),  # Post box
            ]
            
            for by, selector in group_indicators:
                try:
                    self.wait.until(EC.presence_of_element_located((by, selector)))
                    self.logger.info("Successfully navigated to group")
                    return True
                except TimeoutException:
                    continue
            
            self.logger.warning("Group page loaded but couldn't find expected elements")
            return True  # Proceed anyway
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to group: {str(e)}")
            return False
    
    def close(self):
        """Close the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()