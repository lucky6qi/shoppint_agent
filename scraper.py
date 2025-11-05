"""Improved scraper with caching and lightweight requests"""
import json
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests


class AHBonusScraper:
    """Improved scraper with caching and lightweight requests"""
    
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def _load_cache(self) -> Optional[List[Dict[str, Any]]]:
        """Load products from cache if valid"""
        if not os.path.exists(self.config.products_cache_file):
            return None
        
        try:
            with open(self.config.products_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache has timestamp
            if isinstance(cache_data, dict) and 'timestamp' in cache_data:
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                expiry_time = cache_time + timedelta(hours=self.config.cache_expiry_hours)
                
                if datetime.now() < expiry_time:
                    print(f"✅ Using cached products (cached at {cache_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    return cache_data.get('products', [])
                else:
                    print(f"ℹ️ Cache expired (expired at {expiry_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    return None
            else:
                # Old format without timestamp, treat as expired
                return None
                
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
            return None
    
    def _save_cache(self, products: List[Dict[str, Any]]):
        """Save products to cache with timestamp"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'products': products
            }
            with open(self.config.products_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Products cached to {self.config.products_cache_file}")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def _try_lightweight_scrape(self) -> Optional[List[Dict[str, Any]]]:
        """Try to scrape using lightweight requests + BeautifulSoup"""
        print("🔍 Attempting lightweight scrape (requests + BeautifulSoup)...")
        
        try:
            response = self.session.get(
                self.config.ah_bonus_url,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product data in various possible formats
            products = []
            
            # Method 1: Look for JSON-LD or script tags with product data
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Try to extract product data from JSON structure
                    if isinstance(data, dict) and 'products' in data:
                        products = data['products']
                        break
                except:
                    continue
            
            # Method 2: Look for product cards in HTML
            if not products:
                product_cards = soup.find_all(attrs={'data-testhook': 'promotion-card'})
                if not product_cards:
                    # Try alternative selectors
                    product_cards = soup.find_all('div', class_=lambda x: x and 'promotion' in x.lower())
                
                for card in product_cards[:self.config.max_products]:
                    try:
                        product = self._extract_product_from_html(card)
                        if product:
                            products.append(product)
                    except:
                        continue
            
            if products:
                print(f"✅ Lightweight scrape successful: found {len(products)} products")
                return products
            else:
                print("ℹ️ Lightweight scrape found no products (page may be dynamically loaded)")
                return None
                
        except Exception as e:
            print(f"ℹ️ Lightweight scrape failed: {e}")
            print("   Falling back to Selenium...")
            return None
    
    def _extract_product_from_html(self, element) -> Optional[Dict[str, Any]]:
        """Extract product information from HTML element"""
        try:
            # Extract title
            title_elem = element.find(attrs={'data-testhook': 'promotion-card-title'})
            if not title_elem:
                title_elem = element.find('h1') or element.find('h2') or element.find('h3') or element.find('h4')
            
            title = title_elem.get_text(strip=True) if title_elem else ""
            if not title:
                return None
            
            # Extract price
            price_info = self._extract_price_from_html(element)
            
            # Extract description
            desc_elem = element.find(attrs={'data-testhook': 'card-description'})
            description = desc_elem.get_text(strip=True) if desc_elem else title
            
            # Extract image URL
            img_elem = element.find('img')
            image_url = ""
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src') or ""
            
            # Extract product URL
            link_elem = element.find('a', href=True)
            product_url = ""
            if link_elem:
                product_url = link_elem['href']
                if product_url and not product_url.startswith("http"):
                    product_url = self.config.ah_base_url + product_url
            
            return {
                "title": title,
                "price": price_info.get("formatted_price", "Unknown"),
                "current_price": price_info.get("current_price", ""),
                "original_price": price_info.get("original_price", ""),
                "discount": price_info.get("discount_percent", 0),
                "description": description,
                "image_url": image_url,
                "product_url": product_url,
            }
        except:
            return None
    
    def _extract_price_from_html(self, element) -> Dict[str, Any]:
        """Extract price information from HTML element"""
        price_info = {
            "current_price": "",
            "original_price": "",
            "formatted_price": "",
            "discount_percent": 0
        }
        
        try:
            price_elem = element.find(attrs={'data-testhook': 'price'})
            if price_elem:
                current_price = price_elem.get('data-testpricenow')
                original_price = price_elem.get('data-testpricewas')
                
                if current_price:
                    price_info["current_price"] = f"€{current_price}"
                if original_price:
                    price_info["original_price"] = f"€{original_price}"
                
                if current_price and original_price:
                    try:
                        current_float = float(current_price)
                        original_float = float(original_price)
                        discount = round(((original_float - current_float) / original_float) * 100)
                        price_info["discount_percent"] = discount
                        price_info["formatted_price"] = (
                            f"€{current_price} (was €{original_price}, discount {discount}%)"
                        )
                    except:
                        price_info["formatted_price"] = f"€{current_price} (was €{original_price})"
                elif current_price:
                    price_info["formatted_price"] = f"€{current_price}"
                else:
                    price_text = price_elem.get_text(strip=True)
                    if price_text:
                        price_info["formatted_price"] = price_text
        except:
            pass
        
        return price_info
    
    def _setup_driver(self):
        """Setup Chrome driver"""
        if self.driver:
            return
            
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
    
    def scrape_bonus_products(self, use_cache: bool = True, 
                             prefer_lightweight: bool = True) -> List[Dict[str, Any]]:
        """
        Scrape all discount products with improved performance
        
        Args:
            use_cache: Whether to use cache if available
            prefer_lightweight: Whether to try lightweight method first
        
        Returns:
            List of product dictionaries
        """
        print("🔍 Starting to scrape AH.nl/bonus page...")
        
        # Step 1: Check cache
        if use_cache:
            cached_products = self._load_cache()
            if cached_products:
                return cached_products
        
        # Step 2: Try lightweight method first (faster)
        if prefer_lightweight:
            products = self._try_lightweight_scrape()
            if products:
                self._save_cache(products)
                return products
        
        # Step 3: Fallback to Selenium (slower but more reliable)
        print("🌐 Using Selenium (fallback method)...")
        return self._scrape_with_selenium()
    
    def _scrape_with_selenium(self) -> List[Dict[str, Any]]:
        """Scrape using Selenium (original method, improved)"""
        self._setup_driver()
        
        try:
            # Visit bonus page
            print(f"🌐 Visiting: {self.config.ah_bonus_url}")
            self.driver.get(self.config.ah_bonus_url)
            time.sleep(3)  # Wait for page to load
            
            # Accept cookies with multiple strategies
            print("🍪 Looking for cookie consent dialog...")
            cookie_accepted = False
            
            # Strategy 1: Try multiple selectors for Accept button
            accept_selectors = [
                # By text content (most common)
                "//button[contains(text(), 'Accepteren')]",
                "//button[contains(text(), 'Accept')]",
                "//button[normalize-space(text())='Accepteren']",
                "//button[normalize-space(text())='Accept']",
                # By data attributes
                "//button[@data-testhook='cookie-consent-accept']",
                "//button[@data-testid='cookie-accept']",
                # By class names that might contain accept
                "//button[contains(@class, 'accept')]",
                "//button[contains(@class, 'cookie-accept')]",
                # By aria-label
                "//button[@aria-label='Accepteren']",
                "//button[@aria-label='Accept']",
            ]
            
            for selector in accept_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    # Scroll button into view if needed
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
                    time.sleep(0.5)
                    cookie_button.click()
                    print("✅ Cookies accepted")
                    cookie_accepted = True
                    time.sleep(1)  # Wait for dialog to close
                    break
                except:
                    continue
            
            # Strategy 2: Try finding the dialog modal first, then the button inside
            if not cookie_accepted:
                try:
                    # Look for common cookie dialog containers
                    dialog_selectors = [
                        "//div[contains(@class, 'cookie')]",
                        "//div[contains(@class, 'consent')]",
                        "//div[@role='dialog']",
                        "//div[contains(@id, 'cookie')]",
                    ]
                    
                    for dialog_selector in dialog_selectors:
                        try:
                            dialog = self.driver.find_element(By.XPATH, dialog_selector)
                            if dialog.is_displayed():
                                # Find accept button inside the dialog
                                accept_buttons = dialog.find_elements(By.XPATH, 
                                    ".//button[contains(text(), 'Accepteren') or contains(text(), 'Accept')]")
                                if accept_buttons:
                                    accept_button = accept_buttons[0]
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", accept_button)
                                    time.sleep(0.5)
                                    accept_button.click()
                                    print("✅ Cookies accepted (found in dialog)")
                                    cookie_accepted = True
                                    time.sleep(1)
                                    break
                        except:
                            continue
                except:
                    pass
            
            # Strategy 3: Try JavaScript click if regular click doesn't work
            if not cookie_accepted:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//button[contains(text(), 'Accepteren') or contains(text(), 'Accept')]"))
                    )
                    self.driver.execute_script("arguments[0].click();", cookie_button)
                    print("✅ Cookies accepted (via JavaScript)")
                    cookie_accepted = True
                    time.sleep(1)
                except:
                    pass
            
            if not cookie_accepted:
                print("⚠️ Cookie banner not found or could not be accepted - continuing anyway")
            
            # Additional wait to ensure page is ready after cookie acceptance
            time.sleep(1)
            
            # Improved scroll logic with smarter waiting
            print("📜 Scrolling page to load all products...")
            last_count = 0
            scroll_attempts = 0
            max_attempts = 50
            no_change_count = 0
            max_no_change = 3  # Stop after 3 consecutive no-change scrolls
            
            while scroll_attempts < max_attempts:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Smarter wait: check if new content loaded
                time.sleep(1.5)  # Reduced from 2
                
                elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testhook='promotion-card']")
                current_count = len(elements)
                
                if current_count == last_count:
                    no_change_count += 1
                    if no_change_count >= max_no_change:
                        # Try clicking "Load More" button
                        try:
                            load_more = self.driver.find_element(By.XPATH, 
                                "//button[contains(text(), 'Meer laden') or contains(text(), 'Load more')]")
                            if load_more.is_displayed():
                                load_more.click()
                                time.sleep(2)  # Reduced from 3
                                no_change_count = 0
                                continue
                        except:
                            pass
                        
                        # If still no change after load more attempt, stop
                        if no_change_count >= max_no_change:
                            print(f"✅ Loaded all products, total: {current_count}")
                            break
                else:
                    no_change_count = 0
                
                last_count = current_count
                scroll_attempts += 1
                if scroll_attempts % 10 == 0:
                    print(f"   Loaded {current_count} products...")
            
            # Extract product information
            products = []
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "[data-testhook='promotion-card']")
            
            print(f"📦 Extracting information from {len(product_elements)} products...")
            
            failed_extractions = 0
            for i, element in enumerate(product_elements[:self.config.max_products]):
                try:
                    if (i + 1) % 50 == 0:
                        print(f"   Progress: {i+1}/{min(len(product_elements), self.config.max_products)}")
                    
                    # Extract title with multiple fallback strategies
                    title = ""
                    try:
                        title_elem = element.find_element(By.CSS_SELECTOR, 
                            "[data-testhook='promotion-card-title']")
                        title = title_elem.text.strip()
                    except:
                        # Try alternative selectors
                        title_selectors = [
                            "[data-testhook='promotion-card-title']",
                            "[data-testhook*='title']",
                            "[data-testhook*='name']",
                            "h1", "h2", "h3", "h4", "h5",
                            "a[href*='/producten/']",
                            "[class*='title']",
                            "[class*='name']",
                            ".promotion-card-title_root__YObeO",
                            "[class*='promotion-card-title']",
                        ]
                        for selector in title_selectors:
                            try:
                                title_elem = element.find_element(By.CSS_SELECTOR, selector)
                                title = title_elem.text.strip()
                                if title and len(title) > 2:  # Ensure title is meaningful
                                    break
                            except:
                                continue
                    
                    # If still no title, try getting text from the element itself
                    if not title:
                        try:
                            title = element.text.strip().split('\n')[0].strip()
                            if len(title) < 2 or len(title) > 200:  # Sanity check
                                title = ""
                        except:
                            pass
                    
                    if not title:
                        failed_extractions += 1
                        if failed_extractions <= 3:  # Only show first 3 failures for debugging
                            try:
                                element_html = element.get_attribute('outerHTML')[:200]
                                print(f"   ⚠️  Failed to extract title from element {i+1}: {element_html}...")
                            except:
                                pass
                        continue
                    
                    # Extract price
                    price_info = self._extract_price_selenium(element)
                    
                    # Extract description
                    description = ""
                    try:
                        desc_elem = element.find_element(By.CSS_SELECTOR, 
                            "[data-testhook='card-description']")
                        description = desc_elem.text.strip()
                    except:
                        pass
                    
                    # Extract image URL
                    image_url = ""
                    try:
                        img_elem = element.find_element(By.TAG_NAME, "img")
                        image_url = (img_elem.get_attribute("src") or 
                                   img_elem.get_attribute("data-src") or "")
                    except:
                        pass
                    
                    # Extract product URL
                    product_url = ""
                    try:
                        product_url = element.get_attribute("href")
                        if product_url and not product_url.startswith("http"):
                            product_url = self.config.ah_base_url + product_url
                    except:
                        pass
                    
                    product = {
                        "title": title,
                        "price": price_info.get("formatted_price", "Unknown"),
                        "current_price": price_info.get("current_price", ""),
                        "original_price": price_info.get("original_price", ""),
                        "discount": price_info.get("discount_percent", 0),
                        "description": description or title,
                        "image_url": image_url,
                        "product_url": product_url,
                    }
                    
                    products.append(product)
                    
                except Exception as e:
                    continue
            
            print(f"✅ Successfully scraped {len(products)} discount products")
            if failed_extractions > 0:
                print(f"⚠️  Failed to extract {failed_extractions} products (likely due to missing title)")
            self._save_cache(products)
            return products
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _extract_price_selenium(self, element) -> Dict[str, Any]:
        """Extract price information from Selenium element"""
        price_info = {
            "current_price": "",
            "original_price": "",
            "formatted_price": "",
            "discount_percent": 0
        }
        
        try:
            price_elem = element.find_element(By.CSS_SELECTOR, "[data-testhook='price']")
            current_price = price_elem.get_attribute("data-testpricenow")
            original_price = price_elem.get_attribute("data-testpricewas")
            
            if current_price:
                price_info["current_price"] = f"€{current_price}"
            if original_price:
                price_info["original_price"] = f"€{original_price}"
            
            if current_price and original_price:
                try:
                    current_float = float(current_price)
                    original_float = float(original_price)
                    discount = round(((original_float - current_float) / original_float) * 100)
                    price_info["discount_percent"] = discount
                    price_info["formatted_price"] = (
                        f"€{current_price} (was €{original_price}, discount {discount}%)"
                    )
                except:
                    price_info["formatted_price"] = f"€{current_price} (was €{original_price})"
            elif current_price:
                price_info["formatted_price"] = f"€{current_price}"
            else:
                price_text = price_elem.text.strip()
                if price_text:
                    price_info["formatted_price"] = price_text
        except:
            pass
        
        return price_info
    
    def summarize_products(self, products: List[Dict[str, Any]]) -> str:
        """Summarize all discount products"""
        if not products:
            return "No discount products found"
        
        summary = f"📊 AH.nl Discount Products Summary\n"
        summary += f"=" * 50 + "\n"
        summary += f"Total products: {len(products)}\n\n"
        
        # Categorize by discount
        high_discount = [p for p in products if p.get("discount", 0) >= 30]
        medium_discount = [p for p in products if 10 <= p.get("discount", 0) < 30]
        low_discount = [p for p in products if 0 < p.get("discount", 0) < 10]
        
        summary += f"High discount (≥30%): {len(high_discount)} products\n"
        summary += f"Medium discount (10-29%): {len(medium_discount)} products\n"
        summary += f"Low discount (<10%): {len(low_discount)} products\n\n"
        
        # Show top 10 high discount products
        summary += "🔥 Top 10 High Discount Products:\n"
        sorted_products = sorted(products, key=lambda x: x.get("discount", 0), reverse=True)
        for i, product in enumerate(sorted_products[:10], 1):
            summary += f"  {i}. {product['title']} - {product['price']}\n"
        
        return summary
