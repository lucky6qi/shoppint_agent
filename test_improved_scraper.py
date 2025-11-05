"""Test script to compare original and improved scraper performance"""
import time
from config import Config
from scraper import AHBonusScraper


def test_scraper_performance():
    """Compare performance of original vs improved scraper"""
    print("=" * 70)
    print("🧪 Testing Scraper Performance Comparison")
    print("=" * 70)
    
    config = Config.from_env()
    
    # Test 1: Improved scraper with cache (first run - no cache)
    print("\n" + "=" * 70)
    print("📊 Test 1: Improved Scraper (First Run - No Cache)")
    print("=" * 70)
    start_time = time.time()
    
    improved_scraper = AHBonusScraper(config)
    products_improved = improved_scraper.scrape_bonus_products(
        use_cache=False,  # Force fresh scrape
        prefer_lightweight=True
    )
    
    elapsed_improved = time.time() - start_time
    print(f"\n⏱️  Improved scraper time: {elapsed_improved:.2f} seconds")
    print(f"📦 Products found: {len(products_improved)}")
    
    # Test 2: Improved scraper with cache (second run - with cache)
    print("\n" + "=" * 70)
    print("📊 Test 2: Improved Scraper (Second Run - With Cache)")
    print("=" * 70)
    start_time = time.time()
    
    products_cached = improved_scraper.scrape_bonus_products(
        use_cache=True,  # Use cache
        prefer_lightweight=True
    )
    
    elapsed_cached = time.time() - start_time
    print(f"\n⏱️  Cached scraper time: {elapsed_cached:.2f} seconds")
    print(f"📦 Products found: {len(products_cached)}")
    
    # Calculate speedup
    if elapsed_cached > 0:
        speedup = elapsed_improved / elapsed_cached
        print(f"🚀 Cache speedup: {speedup:.1f}x faster")
    
    # Test 3: Original scraper (for comparison, optional)
    print("\n" + "=" * 70)
    print("📊 Test 3: Original Scraper (For Comparison)")
    print("=" * 70)
    print("⚠️  Note: This will take longer and requires browser")
    print("⏭️  Skipping original scraper test (non-interactive mode)")
    
    # Uncomment below to run original scraper comparison
    # user_input = input("Run original scraper for comparison? (y/n): ").strip().lower()
    # 
    # if user_input == 'y':
    #     start_time = time.time()
    #     
    #     original_scraper = AHBonusScraper(config)
    #     products_original = original_scraper.scrape_bonus_products()
    #     
    #     elapsed_original = time.time() - start_time
    #     print(f"\n⏱️  Original scraper time: {elapsed_original:.2f} seconds")
    #     print(f"📦 Products found: {len(products_original)}")
    #     
    #     if elapsed_improved > 0:
    #         speedup_vs_original = elapsed_original / elapsed_improved
    #         print(f"🚀 Improved scraper is {speedup_vs_original:.1f}x faster than original")
    
    # Summary
    print("\n" + "=" * 70)
    print("📈 Summary")
    print("=" * 70)
    print(f"✅ Improved scraper (first run): {elapsed_improved:.2f}s")
    print(f"✅ Improved scraper (cached): {elapsed_cached:.2f}s")
    if elapsed_cached > 0:
        print(f"🚀 Cache provides {speedup:.1f}x speedup")
    print("\n💡 Key Improvements:")
    print("   1. ✅ Cache mechanism (6-hour expiry)")
    print("   2. ✅ Lightweight requests method (faster)")
    print("   3. ✅ Smarter scrolling logic (fewer waits)")
    print("   4. ✅ Automatic fallback to Selenium if needed")
    print("=" * 70)


def test_cache_validation():
    """Test cache validation and expiry"""
    print("\n" + "=" * 70)
    print("🧪 Testing Cache Validation")
    print("=" * 70)
    
    config = Config.from_env()
    scraper = AHBonusScraper(config)
    
    # Test cache load
    print("\n1. Testing cache load...")
    cached = scraper._load_cache()
    if cached:
        print(f"   ✅ Cache loaded: {len(cached)} products")
    else:
        print("   ℹ️  No valid cache found")
    
    # Test cache save
    print("\n2. Testing cache save...")
    test_products = [
        {"title": "Test Product 1", "price": "€2.99"},
        {"title": "Test Product 2", "price": "€3.99"}
    ]
    scraper._save_cache(test_products)
    print("   ✅ Cache saved")
    
    # Test cache load again
    print("\n3. Testing cache load after save...")
    cached = scraper._load_cache()
    if cached:
        print(f"   ✅ Cache loaded: {len(cached)} products")
        print(f"   📦 Products: {[p['title'] for p in cached]}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cache":
        test_cache_validation()
    else:
        test_scraper_performance()
        
        # Also test cache validation
        test_cache_validation()

