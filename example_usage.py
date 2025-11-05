"""Usage examples"""
from config import Config
from scraper import AHBonusScraper
from history import ShoppingHistory
from bucket_generator import BucketGenerator
import os


def example_scrape_only():
    """Example 1: Scrape products only"""
    print("=" * 50)
    print("Example 1: Scrape AH.nl discount products")
    print("=" * 50)
    
    config = Config()
    scraper = AHBonusScraper(config)
    
    products = scraper.scrape_bonus_products()
    summary = scraper.summarize_products(products)
    print(summary)


def example_with_history():
    """Example 2: Scrape products and view history"""
    print("=" * 50)
    print("Example 2: Scrape products and view history")
    print("=" * 50)
    
    config = Config()
    scraper = AHBonusScraper(config)
    history = ShoppingHistory()
    
    # Scrape products
    products = scraper.scrape_bonus_products()
    
    # View history
    print("\n" + history.format_recent_lists(10))


def example_full_workflow():
    """Example 3: Full workflow (including bucket generation)"""
    print("=" * 50)
    print("Example 3: Full workflow")
    print("=" * 50)
    
    config = Config.from_env()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠️ Need to set ANTHROPIC_API_KEY environment variable")
        return
    
    scraper = AHBonusScraper(config)
    history = ShoppingHistory()
    generator = BucketGenerator(api_key)
    
    # Scrape products
    products = scraper.scrape_bonus_products()
    
    # Get history
    recent_lists = history.get_recent_lists(10)
    
    # Generate bucket
    user_requirements = "Buy healthy ingredients for a week, including meat, vegetables, fruits"
    buckets = generator.generate_buckets(
        products=products,
        user_requirements=user_requirements,
        recent_history=recent_lists
    )
    
    print("\n" + generator.format_buckets(buckets))
    
    # Save to history
    all_items = []
    for bucket_items in buckets.values():
        all_items.extend(bucket_items)
    
    history.add_shopping_list(all_items, notes=user_requirements)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
        if example_num == "1":
            example_scrape_only()
        elif example_num == "2":
            example_with_history()
        elif example_num == "3":
            example_full_workflow()
        else:
            print("Usage: python example_usage.py [1|2|3]")
    else:
        print("Select example:")
        print("1. Scrape products only")
        print("2. Scrape products and view history")
        print("3. Full workflow (including bucket generation)")
        print("\nRun: python example_usage.py [1|2|3]")
