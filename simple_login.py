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

def comment_on_recent_posts(driver):
    """Find and comment on the 3 most recent posts."""
    import random
    
    # Human-like variations of your message
    messages = [
        "aqui hay mas trabajos gente www.jobdirecto.com",
        "aqui tambien hay empleos www.jobdirecto.com", 
        "hay encuentran chamba www.jobdirecto.com",
        "mas trabajos por aca www.jobdirecto.com",
        "trabajos aqui tambien www.jobdirecto.com",
        "empleos por aqui gente www.jobdirecto.com"
    ]
    
    print("📝 Looking for posts to comment on...")
    time.sleep(3)
    
    # Scroll down a bit to load more posts
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(2)
    
    # Find post containers - try multiple selectors
    post_selectors = [
        "div[role='article']",
        "div[data-pagelet*='FeedUnit']", 
        "div[data-pagelet*='GroupsFeed']",
        "[data-testid='fbfeed_story']",
        "div[data-testid='story-subtilte']",
        "div[class*='story']"
    ]
    
    posts_found = []
    for selector in post_selectors:
        try:
            posts = driver.find_elements(By.CSS_SELECTOR, selector)
            if posts:
                print(f"✅ Found {len(posts)} potential posts with selector: {selector}")
                
                # Filter to actual posts (should have some text content)
                valid_posts = []
                for i, post in enumerate(posts[:10]):  # Check first 10
                    try:
                        # Check if post has meaningful content
                        post_text = post.text.strip()
                        if len(post_text) > 50:  # Posts should have some content
                            print(f"   📝 Post {i+1} has {len(post_text)} characters")
                            valid_posts.append(post)
                            if len(valid_posts) >= 3:
                                break
                    except:
                        continue
                
                if valid_posts:
                    posts_found = valid_posts
                    print(f"✅ Selected {len(posts_found)} valid posts")
                    break
        except:
            continue
    
    if not posts_found:
        print("❌ No posts found to comment on")
        return
    
    print(f"💬 Starting to comment on {len(posts_found)} posts...")
    
    for i, post in enumerate(posts_found):
        try:
            print(f"\n📝 Commenting on post {i+1}/3...")
            
            # Scroll to the post
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post)
            time.sleep(random.uniform(1, 2))
            
            # Look for comment box in this post
            comment_box = find_comment_box(driver, post)
            if not comment_box:
                print(f"⚠️ Could not find comment box for post {i+1}")
                continue
            
            print(f"✅ Found comment box for post {i+1}")
            
            # Click on comment box to focus it
            print(f"🖱️ Clicking on comment box...")
            try:
                # Try multiple click methods
                comment_box.click()
                time.sleep(1)
            except:
                try:
                    driver.execute_script("arguments[0].click();", comment_box)
                    time.sleep(1)
                except:
                    print(f"❌ Failed to click comment box")
                    continue
            
            # Check if the box is focused
            active_element = driver.switch_to.active_element
            if active_element == comment_box:
                print(f"✅ Comment box is now focused")
            else:
                print(f"⚠️ Comment box might not be focused, trying anyway...")
            
            # Select random message
            message = random.choice(messages)
            print(f"💭 Typing: {message}")
            
            # Clear any existing content first
            try:
                comment_box.clear()
                time.sleep(0.5)
            except:
                # Try alternative clearing methods
                try:
                    comment_box.send_keys("")
                    from selenium.webdriver.common.keys import Keys
                    comment_box.send_keys(Keys.CONTROL + "a")
                    comment_box.send_keys(Keys.DELETE)
                except:
                    pass
            
            # Type message with human-like delays
            success = type_like_human(comment_box, message)
            
            if not success:
                print(f"❌ Failed to type message in post {i+1}")
                continue
            
            # Submit comment
            if submit_comment(driver, post):
                print(f"✅ Successfully commented on post {i+1}")
            else:
                print(f"❌ Failed to submit comment on post {i+1}")
            
            # Wait between comments (human-like)
            delay = random.uniform(15, 25)
            print(f"⏳ Waiting {delay:.1f}s before next comment...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"❌ Error commenting on post {i+1}: {e}")
            continue

def find_comment_box(driver, post):
    """Find comment input box for a specific post."""
    
    print(f"🔍 Analyzing post structure...")
    
    # First, let's see what's actually in this post
    try:
        post_html = post.get_attribute('innerHTML')[:500]  # First 500 chars
        print(f"📄 Post HTML preview: {post_html[:200]}...")
    except:
        pass
    
    # Try to find any interactive elements first
    try:
        all_clickable = post.find_elements(By.CSS_SELECTOR, "[role='button'], button, [tabindex], [onclick]")
        print(f"🖱️ Found {len(all_clickable)} potentially clickable elements")
        
        for i, elem in enumerate(all_clickable[:5]):  # Check first 5
            try:
                text = elem.text.strip()[:50]
                aria_label = elem.get_attribute('aria-label') or ""
                if any(word in text.lower() for word in ['comment', 'write', 'reply']) or \
                   any(word in aria_label.lower() for word in ['comment', 'write', 'reply']):
                    print(f"   🎯 Potential comment trigger {i+1}: '{text}' (aria: '{aria_label}')")
            except:
                pass
    except:
        pass
    
    # Look for comment triggers more aggressively
    comment_trigger_patterns = [
        # English
        ".//span[contains(text(), 'Comment')]",
        ".//div[contains(text(), 'Comment')]", 
        ".//span[contains(text(), 'Write a comment')]",
        ".//div[contains(text(), 'Write a comment')]",
        # Spanish
        ".//span[contains(text(), 'Comentar')]",
        ".//div[contains(text(), 'Comentar')]",
        ".//span[contains(text(), 'Escribe un comentario')]",
        ".//div[contains(text(), 'Escribe un comentario')]",
        # Aria labels
        ".//*[@aria-label='Comment']",
        ".//*[@aria-label='Comentar']",
        ".//*[contains(@aria-label, 'comment')]",
        ".//*[contains(@aria-label, 'comentar')]"
    ]
    
    print(f"🔍 Looking for comment triggers...")
    for i, pattern in enumerate(comment_trigger_patterns):
        try:
            triggers = post.find_elements(By.XPATH, pattern)
            for j, trigger in enumerate(triggers):
                if trigger.is_displayed():
                    trigger_text = trigger.text.strip()
                    aria_label = trigger.get_attribute('aria-label') or ""
                    print(f"   🎯 Found trigger {i+1}.{j+1}: '{trigger_text}' (aria: '{aria_label}')")
                    
                    # Try clicking this trigger
                    try:
                        print(f"   🖱️ Clicking trigger...")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", trigger)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", trigger)
                        time.sleep(2)
                        
                        # Now try to find the comment input that should have appeared
                        comment_selectors = [
                            "div[contenteditable='true'][role='textbox']",
                            "div[contenteditable='true']",
                            "textarea[placeholder*='comment']",
                            "textarea[placeholder*='comentar']",
                            "input[placeholder*='comment']",
                            "input[placeholder*='comentar']"
                        ]
                        
                        for selector in comment_selectors:
                            try:
                                # Look in the whole page now, not just the post
                                comment_boxes = driver.find_elements(By.CSS_SELECTOR, selector)
                                for box in comment_boxes:
                                    if box.is_displayed() and box.is_enabled():
                                        placeholder = box.get_attribute('placeholder') or ""
                                        aria_label = box.get_attribute('aria-label') or ""
                                        print(f"   ✅ Found active comment box! (placeholder: '{placeholder}', aria: '{aria_label}')")
                                        return box
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"   ❌ Error clicking trigger: {e}")
                        continue
        except:
            continue
    
    # If still no luck, try looking for any text input on the page
    print(f"🔍 Searching for ANY text input on page...")
    all_text_inputs = [
        "div[contenteditable='true']",
        "textarea",
        "input[type='text']",
        "*[contenteditable='true']"
    ]
    
    for selector in all_text_inputs:
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"   Found {len(inputs)} elements with selector: {selector}")
            for i, inp in enumerate(inputs):
                try:
                    if inp.is_displayed() and inp.is_enabled():
                        placeholder = inp.get_attribute('placeholder') or ""
                        aria_label = inp.get_attribute('aria-label') or ""
                        tag = inp.tag_name
                        print(f"   💭 Input {i+1}: tag='{tag}', placeholder='{placeholder}', aria='{aria_label}'")
                        
                        # If it looks like a comment box, try it
                        if any(word in placeholder.lower() for word in ['comment', 'comentar', 'write', 'escrib']) or \
                           any(word in aria_label.lower() for word in ['comment', 'comentar', 'write', 'escrib']):
                            print(f"   ✅ This looks like a comment box!")
                            return inp
                except:
                    continue
        except:
            continue
    
    print(f"❌ Still no comment box found")
    return None

def type_like_human(element, text):
    """Type text with human-like delays and patterns."""
    import random
    
    try:
        print(f"🔤 Starting to type: '{text}'")
        
        for i, char in enumerate(text):
            try:
                element.send_keys(char)
                print(f"✓ Typed: '{char}' (char {i+1}/{len(text)})")
                
                # Different delays for different characters
                if char == ' ':
                    time.sleep(random.uniform(0.1, 0.3))  # Longer pause after words
                elif char in '.,!?':
                    time.sleep(random.uniform(0.2, 0.4))  # Pause after punctuation
                else:
                    time.sleep(random.uniform(0.05, 0.15))  # Normal typing
                
                # Occasional thinking pauses
                if random.random() < 0.1 and i > 5:  # 10% chance after 5 chars
                    time.sleep(random.uniform(0.3, 0.8))
                    
            except Exception as e:
                print(f"❌ Error typing character '{char}': {e}")
                return False
        
        print(f"✅ Successfully typed full message")
        return True
        
    except Exception as e:
        print(f"❌ Error in type_like_human: {e}")
        return False

def submit_comment(driver, post):
    """Submit the comment."""
    submit_selectors = [
        "button[type='submit']",
        "button[data-testid='ufi_comment_submit']",
        "[aria-label='Post']",
        "[aria-label='Comment']"
    ]
    
    for selector in submit_selectors:
        try:
            submit_buttons = post.find_elements(By.CSS_SELECTOR, selector)
            for button in submit_buttons:
                if button.is_displayed() and button.is_enabled():
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    return True
        except:
            continue
    
    # Try pressing Enter as fallback
    try:
        comment_box = find_comment_box(driver, post)
        if comment_box:
            from selenium.webdriver.common.keys import Keys
            comment_box.send_keys(Keys.RETURN)
            time.sleep(2)
            return True
    except:
        pass
    
    return False

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
        print("👋 Press Enter when you're logged in and see your Facebook homepage...")
        input()
        
        # Navigate to the group
        group_url = "https://www.facebook.com/groups/426796887732920"
        print(f"🎯 Navigating to your group: {group_url}")
        driver.get(group_url)
        
        print("⏳ Waiting for group page to load...")
        time.sleep(5)
        
        # Click on "Most relevant" dropdown
        try:
            print("📋 Clicking on 'Most relevant' dropdown...")
            most_relevant_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Most relevant']"))
            )
            driver.execute_script("arguments[0].click();", most_relevant_button)
            time.sleep(2)
            
            # Click on "New posts" option
            print("🆕 Selecting 'New posts' filter...")
            new_posts_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='New posts']"))
            )
            driver.execute_script("arguments[0].click();", new_posts_option)
            time.sleep(3)
            
            print("✅ Filtered to show newest posts first!")
            
        except Exception as e:
            print(f"⚠️ Could not change filter (might already be on new posts): {e}")
        
        print("✅ Group page loaded with newest posts!")
        
        # Now find and comment on the 3 most recent posts
        print("\n🔍 Looking for recent posts to comment on...")
        try:
            comment_on_recent_posts(driver)
        except Exception as e:
            print(f"⚠️ Error commenting on posts: {e}")
        
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