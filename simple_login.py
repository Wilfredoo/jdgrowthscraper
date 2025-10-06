#!/usr/bin/env python3
"""
Simple Facebook Login Test
Just logs in and shows the browser so you can see what's happening.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_browser():
    """Set up Chrome browser."""
    print("Setting up Chrome browser...")
    
    chrome_options = Options()
    # Don't run headless so you can see what's happening
    chrome_options.add_argument('--window-size=1200,800')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Remove automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def login_to_facebook(driver):
    """Navigate to Facebook and let user login manually."""
    print("🌐 Going to Facebook...")
    driver.get("https://www.facebook.com")
    
    print("👋 Please click 'Allow cookies' if popup appears")
    print("⏳ Waiting 5 seconds for you to handle cookies...")
    time.sleep(5)
    
    email = os.getenv('FACEBOOK_EMAIL')
    password = os.getenv('FACEBOOK_PASSWORD')
    
    if not email or not password:
        print("❌ No email/password found in .env file")
        return False
    
    try:
        print("📧 Entering email automatically...")
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "email"))
        )
        email_field.clear()
        email_field.send_keys(email)
        time.sleep(1)
        
        print("🔑 Entering password automatically...")
        password_field = driver.find_element(By.ID, "pass")
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)
        
        print("🔄 Clicking login...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "login"))
        )
        driver.execute_script("arguments[0].click();", login_button)
        
        print("⏳ Login submitted! Handle any 2FA/device approval manually...")
        print("👋 Waiting 10 seconds for 2FA, then continuing...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False
    
    # Check if we're logged in by looking for common Facebook homepage elements
    try:
        print("� Checking if login was successful...")
        # Look for various indicators that we're logged in
        success_indicators = [
            "//div[@role='banner']",  # Top navigation
            "//div[@aria-label='Facebook']",  # Facebook logo
            "//a[@aria-label='Home']",  # Home link
            "//div[contains(@aria-label, 'News Feed')]",  # News feed
        ]
        
        for indicator in success_indicators:
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, indicator))
                )
                print("✅ Successfully detected Facebook homepage!")
                return True
            except:
                continue
        
        print("⚠️  Could not confirm login, but continuing anyway...")
        return True  # Continue even if we can't confirm
        
    except Exception as e:
        print(f"⚠️  Error checking login status: {e}")
        return True  # Continue anyway

def main():
    print("🚀 Facebook Login Test")
    print("=" * 30)
    
    driver = setup_browser()
    
    try:
        if login_to_facebook(driver):
            print("\n✅ Login successful! Now you can explore...")
            print("🎯 Next step: Navigate to your group manually")
            print(f"🔗 Group URL: https://www.facebook.com/groups/426796887732920")
            print("\n👀 Browser will stay open for 2 minutes so you can explore")
            print("⏹️  Press Ctrl+C to close early")
            time.sleep(120)  # 2 minutes
        else:
            print("\n❌ Something went wrong")
            print("🔍 Browser will stay open so you can see what happened")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    finally:
        print("🔒 Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()