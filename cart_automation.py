"""Elegant cart automation module"""
import time
from typing import List, Dict, Any, Optional, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass


@dataclass
class CartResult:
    """Cart operation result"""
    success: bool
    added_count: int
    failed_count: int
    failed_products: List[str]
    message: str


class CartAutomation:
    """Cart automation class - elegant and simple interface"""
    
    def __init__(self, base_url: str = "https://www.ah.nl", headless: bool = False):
        """
        Initialize cart automation
        
        Args:
            base_url: AH website base URL
            headless: Whether to use headless mode (False for user viewing and interaction)
        """
        self.base_url = base_url
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Use user profile (optional, for maintaining login state)
        # chrome_options.add_argument("--user-data-dir=/path/to/profile")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.maximize_window()
    
    def _accept_cookies(self):
        """Accept cookies"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'Accepteren') or contains(text(), 'Accept')]"))
            )
            cookie_button.click()
            time.sleep(1)
            return True
        except:
            return False
    
    def _ensure_logged_in(self) -> bool:
        """Ensure user is logged in (if not logged in, prompt user to login)"""
        try:
            # Check if logged in - look for login button or user icon
            login_indicators = [
                "//a[contains(@href, 'inloggen')]",
                "//button[contains(text(), 'Inloggen')]",
                "[data-testhook='login-button']"
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        print("🔐 Detected not logged in")
                        print("💡 Please log in manually in the browser, press ENTER after logging in...")
                        input("Press ENTER to continue...")
                        return True
                except:
                    continue
            
            # If login button not found, may already be logged in
            return True
        except:
            return True
    
    def _find_product_by_url(self, product_url: str) -> bool:
        """Access product page via product URL"""
        try:
            if not product_url.startswith("http"):
                product_url = self.base_url + product_url
            self.driver.get(product_url)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"   ⚠️ Unable to access product page: {e}")
            return False
    
    def _find_product_by_search(self, product_title: str) -> bool:
        """Find product by search"""
        try:
            # Visit homepage
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Find search box
            search_selectors = [
                "[data-testhook='search-input']",
                "input[placeholder*='Zoeken']",
                "input[type='search']",
                ".search-input",
                "#search-input"
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_box.is_displayed():
                        break
                except:
                    continue
            
            if not search_box:
                return False
            
            # Search for product
            search_box.clear()
            search_box.send_keys(product_title)
            search_box.submit()
            time.sleep(3)
            
            # Click first search result
            first_result_selectors = [
                "[data-testhook='product-card']:first-child",
                ".product-card:first-child",
                "[class*='product-card']:first-child"
            ]
            
            for selector in first_result_selectors:
                try:
                    first_result = self.driver.find_element(By.CSS_SELECTOR, selector)
                    first_result.click()
                    time.sleep(2)
                    return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"   ⚠️ Search failed: {e}")
            return False
    
    def _add_to_cart(self) -> bool:
        """Add product to cart on current product page"""
        add_button_selectors = [
            # Prefer SVG plus button
            "svg.plus-button_icon__cSPiv",
            "button svg.plus-button_icon__cSPiv",
            "button:has(svg.plus-button_icon__cSPiv)",
            # Standard add button
            "[data-testhook='add-to-cart-button']",
            "[data-test-id='add-to-cart']",
            ".add-to-cart-button",
            "button[aria-label*='toevoegen']",
            "button[title*='toevoegen']",
            "button[aria-label*='winkelmandje']",
            ".ah-button--primary"
        ]
        
        for selector in add_button_selectors:
            try:
                if ":has(" in selector:
                    # Use XPath instead of CSS :has()
                    xpath = "//button[.//svg[contains(@class, 'plus-button')]]"
                    add_button = self.driver.find_element(By.XPATH, xpath)
                elif "svg" in selector:
                    # SVG button, find parent button
                    svg_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    add_button = svg_elem.find_element(By.XPATH, "./ancestor::button")
                else:
                    add_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                if add_button.is_displayed() and add_button.is_enabled():
                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_button)
                    time.sleep(0.5)
                    
                    # Try clicking
                    try:
                        add_button.click()
                    except:
                        # JavaScript click as fallback
                        self.driver.execute_script("arguments[0].click();", add_button)
                    
                    time.sleep(1)  # Wait for cart to update
                    return True
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                continue
        
        return False
    
    def add_products(self, products: List[Dict[str, Any]], 
                    progress_callback: Optional[Callable[[str, bool], None]] = None) -> CartResult:
        """
        Batch add products to cart - main interface
        
        Args:
            products: Product list, each product should contain 'title' and optional 'product_url'
            progress_callback: Progress callback function callback(product_title, success)
        
        Returns:
            CartResult: Operation result
        """
        if not self.driver:
            self._setup_driver()
        
        # Visit homepage and accept cookies
        print("🌐 Visiting AH.nl...")
        self.driver.get(self.base_url)
        time.sleep(2)
        
        self._accept_cookies()
        
        # Ensure logged in
        self._ensure_logged_in()
        
        # Start adding products
        print(f"\n🛒 Starting to add {len(products)} products to cart...")
        print("=" * 50)
        
        added_count = 0
        failed_products = []
        
        for i, product in enumerate(products, 1):
            title = product.get("title", "Unknown product")
            product_url = product.get("product_url", "")
            
            print(f"\n[{i}/{len(products)}] {title}")
            
            success = False
            
            # Method 1: If URL exists, access directly
            if product_url:
                if self._find_product_by_url(product_url):
                    success = self._add_to_cart()
            
            # Method 2: If no URL or method 1 failed, try search
            if not success:
                if self._find_product_by_search(title):
                    success = self._add_to_cart()
            
            if success:
                added_count += 1
                print(f"   ✅ Added to cart")
                if progress_callback:
                    progress_callback(title, True)
            else:
                failed_products.append(title)
                print(f"   ❌ Failed to add")
                if progress_callback:
                    progress_callback(title, False)
            
            # Short delay to avoid too fast operations
            time.sleep(1)
        
        # Summary
        result = CartResult(
            success=added_count > 0,
            added_count=added_count,
            failed_count=len(failed_products),
            failed_products=failed_products,
            message=f"Successfully added {added_count}/{len(products)} products"
        )
        
        print("\n" + "=" * 50)
        print(f"✅ Complete! {result.message}")
        if failed_products:
            print(f"\n❌ Failed products ({len(failed_products)} items):")
            for product in failed_products:
                print(f"   - {product}")
        
        return result
    
    def add_from_buckets(self, buckets: Dict[str, List[Dict[str, Any]]],
                        progress_callback: Optional[Callable[[str, bool], None]] = None) -> CartResult:
        """
        Add products from buckets to cart - convenient method
        
        Args:
            buckets: Bucket dictionary, format like {"essentials": [...], "meat": [...]}
            progress_callback: Progress callback function
        
        Returns:
            CartResult: Operation result
        """
        # Merge all products from buckets
        all_products = []
        for bucket_name, items in buckets.items():
            all_products.extend(items)
        
        print(f"📦 Extracted {len(all_products)} products from {len(buckets)} buckets")
        
        return self.add_products(all_products, progress_callback)
    
    def view_cart(self):
        """View cart"""
        try:
            cart_selectors = [
                "[data-testhook='cart-button']",
                "[aria-label*='winkelmandje']",
                "a[href*='/winkelmandje']",
                ".cart-button"
            ]
            
            for selector in cart_selectors:
                try:
                    cart_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if cart_button.is_displayed():
                        cart_button.click()
                        time.sleep(2)
                        print("✅ Cart page opened")
                        return True
                except:
                    continue
            
            # If button not found, directly access cart URL
            self.driver.get(f"{self.base_url}/winkelmandje")
            time.sleep(2)
            print("✅ Cart page opened")
            return True
        except Exception as e:
            print(f"❌ Unable to open cart: {e}")
            return False
    
    def close(self):
        """Close browser (optional, default keeps open for viewing)"""
        if self.driver:
            print("\n💡 Browser will remain open, you can view the cart")
            print("   To close, please manually close the browser window")
            # If auto-close needed, uncomment below
            # self.driver.quit()
            # self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def add_to_cart_simple(products: List[Dict[str, Any]], 
                       headless: bool = False) -> CartResult:
    """
    Simple one-click add products to cart
    
    Args:
        products: Product list
        headless: Whether to use headless mode
    
    Returns:
        CartResult: Operation result
    
    Example:
        >>> products = [
        ...     {"title": "AH Halfvolle melk", "product_url": "https://..."},
        ...     {"title": "AH Eieren", "product_url": "https://..."}
        ... ]
        >>> result = add_to_cart_simple(products)
        >>> print(f"Successfully added {result.added_count} products")
    """
    with CartAutomation(headless=headless) as cart:
        return cart.add_products(products)


def add_buckets_to_cart(buckets: Dict[str, List[Dict[str, Any]]],
                        headless: bool = False) -> CartResult:
    """
    One-click add products from buckets to cart
    
    Args:
        buckets: Bucket dictionary
        headless: Whether to use headless mode
    
    Returns:
        CartResult: Operation result
    
    Example:
        >>> buckets = {
        ...     "essentials": [{"title": "Melk", ...}],
        ...     "meat": [{"title": "Kip", ...}]
        ... }
        >>> result = add_buckets_to_cart(buckets)
    """
    with CartAutomation(headless=headless) as cart:
        return cart.add_from_buckets(buckets)
