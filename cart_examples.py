"""Cart automation usage examples"""
import os
from config import Config
from scraper import AHBonusScraper
from bucket_generator import BucketGenerator
from cart_automation import CartAutomation, add_to_cart_simple, add_buckets_to_cart


def example_simple_add():
    """Example 1: Simple add products to cart"""
    print("=" * 60)
    print("Example 1: Simple add products to cart")
    print("=" * 60)
    
    # Prepare product list
    products = [
        {"title": "AH Halfvolle melk 1 liter", "product_url": ""},
        {"title": "AH Scharreleieren 10 stuks", "product_url": ""},
        {"title": "AH Bruin brood", "product_url": ""}
    ]
    
    # One-click add
    result = add_to_cart_simple(products, headless=False)
    
    print(f"\n✅ Successfully added {result.added_count} products")
    if result.failed_products:
        print(f"❌ Failed: {result.failed_products}")


def example_with_callback():
    """Example 2: Using progress callback"""
    print("=" * 60)
    print("Example 2: Add with progress callback")
    print("=" * 60)
    
    products = [
        {"title": "AH Halfvolle melk", "product_url": ""},
        {"title": "AH Eieren", "product_url": ""}
    ]
    
    def progress_callback(product_title, success):
        """Progress callback function"""
        status = "✅" if success else "❌"
        print(f"   {status} {product_title}")
    
    with CartAutomation() as cart:
        result = cart.add_products(products, progress_callback=progress_callback)
    
    print(f"\nSummary: {result.message}")


def example_full_workflow():
    """Example 3: Full workflow - Scrape -> Generate bucket -> Add to cart"""
    print("=" * 60)
    print("Example 3: Full automation workflow")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️ Need to set ANTHROPIC_API_KEY environment variable")
        return
    
    # 1. Initialize
    config = Config()
    scraper = AHBonusScraper(config)
    generator = BucketGenerator(api_key)
    
    # 2. Scrape products (or load from cache)
    print("\n📊 Step 1: Get products...")
    import json
    products = []
    if os.path.exists(config.products_cache_file):
        with open(config.products_cache_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        print(f"✅ Loaded {len(products)} products from cache")
    else:
        print("⚠️ Cache not found, please run scraper first")
        return
    
    # 3. Generate bucket
    print("\n🤖 Step 2: Generate shopping bucket...")
    buckets = generator.generate_buckets(
        products=products[:100],  # Limit quantity for efficiency
        user_requirements="Buy healthy ingredients for a week, including meat, vegetables, fruits, and essentials"
    )
    
    print(generator.format_buckets(buckets))
    
    # 4. Add to cart
    print("\n🛒 Step 3: Add products to cart...")
    result = add_buckets_to_cart(buckets, headless=False)
    
    print(f"\n✅ Complete! {result.message}")
    
    if result.failed_products:
        print(f"\n❌ Failed products:")
        for product in result.failed_products:
            print(f"   - {product}")


def example_selective_add():
    """Example 4: Selective add (let user choose which buckets)"""
    print("=" * 60)
    print("Example 4: Selective add")
    print("=" * 60)
    
    # Assume buckets already exist
    buckets = {
        "essentials": [
            {"title": "AH Halfvolle melk", "product_url": ""},
            {"title": "AH Eieren", "product_url": ""}
        ],
        "meat": [
            {"title": "AH Kipfilet", "product_url": ""}
        ],
        "vegetables": [
            {"title": "AH Tomaat", "product_url": ""}
        ]
    }
    
    # Let user choose which buckets to add
    print("\nAvailable buckets:")
    for i, bucket_name in enumerate(buckets.keys(), 1):
        print(f"  {i}. {bucket_name} ({len(buckets[bucket_name])} items)")
    
    choice = input("\nSelect buckets to add (enter numbers, comma-separated, or 'all' for all): ").strip()
    
    selected_buckets = {}
    if choice.lower() == 'all':
        selected_buckets = buckets
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(',')]
            bucket_names = list(buckets.keys())
            for idx in indices:
                if 0 <= idx < len(bucket_names):
                    name = bucket_names[idx]
                    selected_buckets[name] = buckets[name]
        except:
            print("❌ Invalid selection")
            return
    
    if selected_buckets:
        print(f"\n🛒 Adding products from {len(selected_buckets)} buckets to cart...")
        result = add_buckets_to_cart(selected_buckets)
        print(f"\n✅ {result.message}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num == "1":
            example_simple_add()
        elif example_num == "2":
            example_with_callback()
        elif example_num == "3":
            example_full_workflow()
        elif example_num == "4":
            example_selective_add()
        else:
            print("Usage: python cart_examples.py [1|2|3|4]")
    else:
        print("Select example:")
        print("1. Simple add products")
        print("2. Add with progress callback")
        print("3. Full automation workflow")
        print("4. Selective add")
        print("\nRun: python cart_examples.py [1|2|3|4]")
