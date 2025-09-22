#!/usr/bin/env python3
"""
Simple Video Scraper - Single Subcategory Processing
Clicks on videos one by one, extracts prompts from popups, closes them, and moves to next video
"""

import os
import csv
import json
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleVideoScraper:
    def __init__(self):
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with optimized options for performance"""
        try:
            # Only create driver if it doesn't exist or is closed
            if self.driver is None:
                chrome_options = Options()
                
                # Performance optimizations
                chrome_options.add_argument("--headless")  # Run in headless mode for speed
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                chrome_options.add_argument("--disable-features=TranslateUI")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                
                # Memory and CPU optimizations
                chrome_options.add_argument("--memory-pressure-off")
                chrome_options.add_argument("--max_old_space_size=4096")
                chrome_options.add_argument("--aggressive-cache-discard")
                
                # Network optimizations
                chrome_options.add_argument("--disable-background-networking")
                chrome_options.add_argument("--disable-default-apps")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-sync")
                chrome_options.add_argument("--disable-translate")
                chrome_options.add_argument("--hide-scrollbars")
                chrome_options.add_argument("--metrics-recording-only")
                chrome_options.add_argument("--mute-audio")
                chrome_options.add_argument("--no-first-run")
                chrome_options.add_argument("--safebrowsing-disable-auto-update")
                
                # Window and display settings
                chrome_options.add_argument("--window-size=1280,720")  # Smaller window for better performance
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Additional performance settings
                chrome_options.add_experimental_option("useAutomationExtension", False)
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                # Disable images and CSS for faster loading (optional - comment out if needed)
                prefs = {
                    "profile.managed_default_content_settings.images": 2,  # Block images
                    "profile.default_content_setting_values.notifications": 2,  # Block notifications
                    "profile.managed_default_content_settings.stylesheets": 2,  # Block CSS (optional)
                }
                chrome_options.add_experimental_option("prefs", prefs)
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Optimized timeouts for faster execution
                self.driver.implicitly_wait(5)  # Reduced from 10
                self.driver.set_page_load_timeout(15)  # Reduced from 30
                
                logger.info("✅ Chrome driver setup complete (headless mode with performance optimizations)")
            
        except Exception as e:
            logger.error(f"❌ Error setting up driver: {str(e)}")
            raise

    def scrape_single_subcategory(self, subcategory_url):
        """Scrape a single subcategory by clicking figure elements one by one"""
        try:
            logger.info(f"🎯 Starting to scrape subcategory: {subcategory_url}")
            
            # Setup driver (reuse if exists)
            self.setup_driver()
            
            # Navigate to subcategory page with better error handling
            logger.info("🌐 Navigating to subcategory page...")
            try:
                self.driver.get(subcategory_url)
                logger.info(f"✅ Successfully loaded URL: {subcategory_url}")
                
                # Check if page loaded properly
                current_url = self.driver.current_url
                logger.info(f"📍 Current URL after navigation: {current_url}")
                
                # Check page title
                page_title = self.driver.title
                logger.info(f"📄 Page title: {page_title}")
                
                # Wait for page to be ready
                wait = WebDriverWait(self.driver, 10)  # Reduced from 15
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                logger.info("✅ Page body loaded successfully")
                
            except Exception as nav_error:
                logger.error(f"❌ Navigation error: {str(nav_error)}")
                logger.error(f"❌ Failed to load URL: {subcategory_url}")
                
                # Try to get current URL and page source for debugging
                try:
                    current_url = self.driver.current_url
                    logger.info(f"📍 Current URL after failed navigation: {current_url}")
                    
                    page_source_length = len(self.driver.page_source)
                    logger.info(f"📄 Page source length: {page_source_length} characters")
                    
                    if page_source_length < 100:
                        logger.warning("⚠️ Page source is very short, possible loading issue")
                        
                except Exception as debug_error:
                    logger.error(f"❌ Could not get debug info: {str(debug_error)}")
                
                raise nav_error
            
            # Reduced wait time for page loading
            time.sleep(2)  # Reduced from 5 seconds
            logger.info("📄 Page loaded, looking for figure elements...")
            
            # Find all figure elements that contain videos
            figure_selector = 'figure[class*="group"][data-sentry-component="MediaFigure"]'
            
            try:
                # Use shorter wait for finding elements
                wait = WebDriverWait(self.driver, 5)  # Reduced wait time
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, figure_selector)))
                figures = self.driver.find_elements(By.CSS_SELECTOR, figure_selector)
                
                if not figures:
                    # Fallback to any figure elements
                    figures = self.driver.find_elements(By.TAG_NAME, "figure")
                    
                if not figures:
                    logger.warning("⚠️ No figure elements found on page")
                    return []
                    
                logger.info(f"🎬 Found {len(figures)} figure elements")
                
            except Exception as e:
                logger.error(f"❌ Error finding figures: {str(e)}")
                return []
            
            videos_data = []
            
            # Performance tracking
            loop_start_time = time.time()
            
            # Process each figure one by one
            for i, figure in enumerate(figures):
                try:
                    figure_start_time = time.time()
                    logger.info(f"🎥 Processing figure {i+1}/{len(figures)}")
                    # Extract video URL directly from the figure's video element
                    video_url = None
                    try:
                        video_element = figure.find_element(By.CSS_SELECTOR, "video[src]")
                        video_url = video_element.get_attribute('src')
                        logger.info(f"🎬 Found video URL in figure: {video_url}")
                    except:
                        logger.debug("No video URL found in figure")
                    
                    # Find the clickable link within the figure
                    clickable_link = None
                    try:
                        clickable_link = figure.find_element(By.CSS_SELECTOR, "a")
                    except:
                        logger.warning(f"⚠️ No clickable link found in figure {i+1}")
                        continue
                    
                    # Scroll to figure to ensure it's visible
                    scroll_start = time.time()
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", figure)
                    time.sleep(1)  # Reduced from 2 seconds
                    scroll_time = time.time() - scroll_start
                    logger.debug(f"⏱️ Scroll time: {scroll_time:.2f}s")
                    
                    # Try multiple click methods on the link
                    click_start = time.time()
                    clicked = False
                    try:
                        # Method 1: Regular click
                        clickable_link.click()
                        clicked = True
                        logger.info("✅ Clicked figure link (regular click)")
                    except:
                        try:
                            # Method 2: JavaScript click
                            self.driver.execute_script("arguments[0].click();", clickable_link)
                            clicked = True
                            logger.info("✅ Clicked figure link (JavaScript click)")
                        except:
                            try:
                                # Method 3: Action chains
                                ActionChains(self.driver).move_to_element(clickable_link).click().perform()
                                clicked = True
                                logger.info("✅ Clicked figure link (ActionChains)")
                            except Exception as e:
                                logger.error(f"❌ Failed to click video link: {e}")
                                continue
                    
                    click_time = time.time() - click_start
                    logger.debug(f"⏱️ Click time: {click_time:.2f}s")
                    
                    if not clicked:
                        logger.warning(f"⚠️ Could not click figure {i+1}, skipping")
                        continue
                    
                    # Wait for popup/modal to appear
                    time.sleep(5)
                    
                    # Extract prompt and video URL from popup
                    extracted_data = self.extract_prompt_from_popup()
                    
                    if extracted_data and (extracted_data.get('prompt') or extracted_data.get('video_url')):
                        # Use video URL from popup if available, otherwise use the one from figure
                        final_video_url = extracted_data.get('video_url') or video_url
                        
                        videos_data.append({
                            'video_url': final_video_url,
                            'prompt': extracted_data.get('prompt', 'No prompt found')
                        })
                        
                        prompt_preview = extracted_data.get('prompt', 'No prompt')[:50] if extracted_data.get('prompt') else 'No prompt'
                        logger.info(f"✅ Extracted data for figure {i+1}: {prompt_preview}...")
                        if final_video_url:
                            logger.info(f"🎬 Video URL: {final_video_url}")
                    else:
                        logger.warning(f"⚠️ No data found for figure {i+1}")
                    
                    # Close popup and return to main page
                    self.close_popup()
                    
                    # Wait a bit before processing next figure
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing video {i+1}: {str(e)}")
                    # Try to close any open popup and continue
                    try:
                        self.close_popup()
                    except:
                        pass
                    continue
            
            total_time = time.time() - loop_start_time
            logger.info(f"🎉 Successfully processed {len(videos_data)} videos from subcategory")
            logger.info(f"⏱️ Total scraping time: {total_time:.2f}s (avg: {total_time/len(figures):.2f}s per video)")
            return videos_data
            
        except Exception as e:
            logger.error(f"❌ Error scraping subcategory: {str(e)}")
            return []

    def extract_prompt_from_popup(self):
        """Extract prompt and video URL from the popup modal."""
        try:
            # Wait for modal to appear
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[role='dialog'], .modal, [data-modal]"))
            )
            logger.debug("Modal found")
            
            # Extract video URL from the modal's video element
            video_url = None
            try:
                video_element = modal.find_element(By.CSS_SELECTOR, "video[src]")
                video_url = video_element.get_attribute('src')
                logger.info(f"🎬 Found video URL in modal: {video_url}")
            except:
                logger.debug("No video URL found in modal")
            
            # Extract prompt text
            prompt = None
            try:
                # Look for the copy prompt button and get its text content
                copy_button = modal.find_element(By.CSS_SELECTOR, "[data-copy-prompt]")
                prompt = copy_button.text.strip()
                if not prompt or prompt == "true":
                    # If button text is empty or "true", try to get the actual prompt text from nearby elements
                    try:
                        # Look for prompt text near the copy button
                        prompt_container = copy_button.find_element(By.XPATH, "./preceding-sibling::*[1] | ./following-sibling::*[1] | ./parent::*/preceding-sibling::*[1]")
                        prompt = prompt_container.text.strip()
                    except:
                        pass
                logger.info(f"📝 Found prompt via copy button: {prompt[:50]}...")
            except:
                # Fallback: look for other prompt selectors
                try:
                    prompt_element = modal.find_element(By.CSS_SELECTOR, ".prompt, [data-prompt], .description, p")
                    prompt = prompt_element.text.strip()
                    logger.info(f"📝 Found prompt via fallback: {prompt[:50]}...")
                except:
                    logger.debug("No prompt found in modal")
            
            return {
                'video_url': video_url,
                'prompt': prompt
            }
            
        except Exception as e:
            logger.error(f"Error extracting data from popup: {e}")
            return None

    def close_popup(self):
        """Close any open popup/modal"""
        try:
            # Wait a moment for popup to be fully loaded
            time.sleep(2)
            
            # Primary method: Click anywhere on the screen to close modal
            try:
                logger.info("🔍 Trying to close modal by clicking anywhere on screen...")
                # Click on the body element (anywhere on the page)
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.click()
                logger.info("🔒 Closed popup by clicking on screen")
                time.sleep(2)
                return True
            except Exception as e:
                logger.debug(f"Screen click failed: {e}")
            
            # Fallback: Try clicking on different areas of the screen
            try:
                # Click at different coordinates on the screen
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                
                # Get window size
                window_size = self.driver.get_window_size()
                width = window_size['width']
                height = window_size['height']
                
                # Try clicking at various positions
                click_positions = [
                    (width // 4, height // 4),      # Top-left area
                    (3 * width // 4, height // 4),  # Top-right area
                    (width // 2, height // 2),      # Center
                    (width // 4, 3 * height // 4),  # Bottom-left area
                    (3 * width // 4, 3 * height // 4)  # Bottom-right area
                ]
                
                for x, y in click_positions:
                    try:
                        actions.move_by_offset(x - width//2, y - height//2).click().perform()
                        logger.info(f"🔒 Closed popup by clicking at position ({x}, {y})")
                        time.sleep(2)
                        return True
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"Position click failed: {e}")
            
            # Enhanced close button selectors including more specific ones
            close_selectors = [
                # Standard close buttons
                "[aria-label='Close']",
                "[aria-label='close']",
                "button[aria-label*='Close' i]",
                "button[aria-label*='close' i]",
                # Common class patterns
                ".close",
                ".close-button",
                "[class*='close']",
                "button[class*='close']",
                ".modal-close",
                "[data-testid='close']",
                "[data-testid='Close']",
                ".x-button",
                "[title='Close']",
                "[title='close']",
                # SVG close icons
                "svg[class*='close']",
                "button svg",
                # Generic buttons that might be close buttons
                "button[type='button']:not([data-copy-prompt])",
                # Back/return buttons
                "button[aria-label*='back' i]",
                "button[aria-label*='return' i]"
            ]
            
            logger.info("🔍 Looking for close button...")
            
            for selector in close_selectors:
                try:
                    close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for close_button in close_buttons:
                        if close_button.is_displayed() and close_button.is_enabled():
                            try:
                                # Try regular click first
                                close_button.click()
                                logger.info(f"🔒 Closed popup with selector: {selector}")
                                time.sleep(2)
                                return True
                            except:
                                try:
                                    # Try JavaScript click
                                    self.driver.execute_script("arguments[0].click();", close_button)
                                    logger.info(f"🔒 Closed popup with JS click: {selector}")
                                    time.sleep(2)
                                    return True
                                except:
                                    continue
                except:
                    continue
            
            # Try pressing Escape key multiple times
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                for _ in range(3):
                    body.send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                logger.info("🔒 Closed popup with Escape key")
                time.sleep(2)
                return True
            except:
                pass
            
            # Try clicking outside the modal (on overlay/backdrop)
            try:
                overlays = self.driver.find_elements(By.CSS_SELECTOR, "[class*='overlay'], [class*='backdrop'], [class*='modal-backdrop']")
                for overlay in overlays:
                    if overlay.is_displayed():
                        try:
                            overlay.click()
                            logger.info("🔒 Closed popup by clicking overlay")
                            time.sleep(2)
                            return True
                        except:
                            continue
            except:
                pass
            
            # Try browser back button as last resort
            try:
                self.driver.back()
                logger.info("🔒 Closed popup with browser back")
                time.sleep(3)
                return True
            except:
                pass
            
            logger.warning("⚠️ Could not find close button for popup")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error closing popup: {str(e)}")
            return False

    def save_videos_data(self, videos_data, category_name="videos"):
        """Save videos data to JSON and CSV files"""
        if not videos_data:
            logger.warning("⚠️ No videos data to save")
            return
        
        # Parse category and subcategory from category_name (format: "Category_Subcategory")
        if "_" in category_name:
            category, subcategory = category_name.split("_", 1)
            # Create folder structure: Category/Subcategory
            folder_path = os.path.join(category, subcategory)
        else:
            # Fallback to original behavior if no underscore
            safe_name = "".join(c for c in category_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            folder_path = safe_name
        
        os.makedirs(folder_path, exist_ok=True)
        
        # Save as JSON
        json_path = os.path.join(folder_path, 'videos.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(videos_data, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_path = os.path.join(folder_path, 'videos.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['video_url', 'prompt']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for video in videos_data:
                writer.writerow({
                    'video_url': video['video_url'],
                    'prompt': video['prompt']
                })
        
        logger.info(f"💾 Saved {len(videos_data)} videos to {folder_path}/")

    def load_subcategories_from_metadata(self, category_folder):
        """Load subcategories from a category's metadata.json file"""
        metadata_path = os.path.join(category_folder, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            logger.error(f"❌ {metadata_path} not found!")
            return []
        
        try:
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                subcategories = data.get('sub_categories', [])
                logger.info(f"📁 Loaded {len(subcategories)} subcategories from {category_folder}")
                return subcategories
        except Exception as e:
            logger.error(f"❌ Error loading {metadata_path}: {e}")
            return []

    def process_category(self, category_name, process_all_subcategories=False):
        """Process a single category or all its subcategories consecutively"""
        try:
            subcategories = self.load_subcategories_from_metadata(category_name)
            if not subcategories:
                logger.error(f"❌ No subcategories found in {category_name}")
                return
            
            logger.info(f"📂 Processing category: {category_name} ({len(subcategories)} subcategories)")
            
            for i, subcat in enumerate(subcategories, 1):
                logger.info(f"🎬 Processing subcategory {i}/{len(subcategories)}: {subcat['name']}")
                logger.info(f"🔗 URL: {subcat['link']}")
                
                try:
                    videos_data = self.scrape_single_subcategory(subcat['link'])
                    
                    if videos_data:
                        # Save with proper category and subcategory names
                        folder_name = f"{category_name}_{subcat['name']}"
                        self.save_videos_data(videos_data, folder_name)
                        logger.info(f"✅ Completed {subcat['name']}: {len(videos_data)} videos extracted")
                    else:
                        logger.warning(f"⚠️ No videos extracted from {subcat['name']}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {subcat['name']}: {str(e)}")
                    continue
                    
                # Small delay between subcategories to avoid overwhelming the server
                if i < len(subcategories):
                    logger.info("⏳ Waiting 5 seconds before next subcategory...")
                    time.sleep(5)
                    
            logger.info(f"🎉 Finished processing all subcategories in {category_name}")
            
        except Exception as e:
            logger.error(f"❌ Error processing category {category_name}: {str(e)}")
        finally:
            # Clean up driver after processing all subcategories
            try:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                    logger.info("🔒 Driver closed after category processing")
            except:
                pass

    def list_available_categories(self):
        """List all available categories with metadata.json files"""
        categories = []
        for item in os.listdir('.'):
            if os.path.isdir(item) and os.path.exists(os.path.join(item, 'metadata.json')):
                categories.append(item)
        return sorted(categories)

    def run(self):
        """Main execution method"""
        try:
            logger.info("🚀 Starting Simple Video Scraper - Single Subcategory Mode")
            
            # List available categories
            categories = self.list_available_categories()
            if not categories:
                logger.error("❌ No categories with metadata.json found!")
                return
            
            print("\n📂 Available categories:")
            print("  0. All categories (process consecutively)")
            for i, category in enumerate(categories, 1):
                print(f"  {i}. {category}")
            
            # Get category choice
            try:
                choice = int(input(f"\nSelect category (0-{len(categories)}): ").strip())
                if choice == 0:
                    # Process all categories consecutively
                    logger.info("🔄 Processing all categories consecutively...")
                    for category in categories:
                        logger.info(f"\n📂 Processing category: {category}")
                        self.process_category(category, process_all_subcategories=True)
                    logger.info("🎉 All categories processed!")
                    return
                elif 1 <= choice <= len(categories):
                    selected_category = categories[choice - 1]
                else:
                    logger.error("❌ Invalid category selection")
                    return
            except ValueError:
                logger.error("❌ Please enter a valid number")
                return
            
            # Load subcategories from selected category
            subcategories = self.load_subcategories_from_metadata(selected_category)
            if not subcategories:
                logger.error(f"❌ No subcategories found in {selected_category}")
                return
            
            print(f"\n🎬 Available subcategories in {selected_category}:")
            print("  0. All subcategories (process consecutively)")
            for i, subcat in enumerate(subcategories, 1):
                print(f"  {i}. {subcat['name']}")
            
            # Get subcategory choice
            try:
                choice = int(input(f"\nSelect subcategory (0-{len(subcategories)}): ").strip())
                if choice == 0:
                    # Process all subcategories consecutively
                    self.process_category(selected_category, process_all_subcategories=True)
                    return
                elif 1 <= choice <= len(subcategories):
                    selected_subcat = subcategories[choice - 1]
                else:
                    logger.error("❌ Invalid subcategory selection")
                    return
            except ValueError:
                logger.error("❌ Please enter a valid number")
                return
            
            # Scrape the selected subcategory
            logger.info(f"🎯 Selected: {selected_subcat['name']} from {selected_category}")
            logger.info(f"🔗 URL: {selected_subcat['link']}")
            
            videos_data = self.scrape_single_subcategory(selected_subcat['link'])
            
            if videos_data:
                # Save with proper category and subcategory names
                folder_name = f"{selected_category}_{selected_subcat['name']}"
                self.save_videos_data(videos_data, folder_name)
                logger.info(f"🎉 Scraping completed! Extracted {len(videos_data)} videos")
            else:
                logger.warning("⚠️ No videos were extracted")
                
        except KeyboardInterrupt:
            logger.info("🛑 Scraping interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in main execution: {str(e)}")

if __name__ == "__main__":
    scraper = SimpleVideoScraper()
    scraper.run()