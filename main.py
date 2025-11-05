"""Main program entry"""
import os
from config import Config
from scraper import AHBonusScraper
from history import ShoppingHistory
from bucket_generator import BucketGenerator
from cart_automation import CartAutomation, add_buckets_to_cart


def main():
    """Main function"""
    print("🛒 AH Shopping Agent")
    print("=" * 50)
    
    # Load configuration
    config = Config.from_env()
    # ═══════════════════════════════════════════════════════════
    # 🔴 LLM CONFIGURATION - Check for Anthropic API key
    # ═══════════════════════════════════════════════════════════
    if not config.anthropic_api_key:
        config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not config.anthropic_api_key:
            print("⚠️ Warning: ANTHROPIC_API_KEY not set, bucket generation will be unavailable")
    
    # Initialize components
    scraper = AHBonusScraper(config)
    history = ShoppingHistory(config.shopping_history_file)
    
    # 1. Scrape discount products
    print("\n📊 Step 1: Scraping AH.nl/bonus products...")
    products = scraper.scrape_bonus_products()
    
    if not products:
        print("❌ No products found, exiting")
        return
    
    # Save products to cache
    try:
        import json
        with open(config.products_cache_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"✅ Product data cached to {config.products_cache_file}")
    except:
        pass
    
    # 2. Summarize product information
    print("\n📝 Step 2: Generating product summary...")
    summary = scraper.summarize_products(products)
    print(summary)
    
    # 3. Get recent 10 shopping lists
    print("\n📋 Step 3: Getting recent 10 shopping lists...")
    recent_lists = history.get_recent_lists(10)
    if recent_lists:
        print(history.format_recent_lists(10))
    else:
        print("ℹ️ No shopping history")
    
    # 4. Generate base bucket
    # ═══════════════════════════════════════════════════════════
    # 🔴 LLM USAGE - Generate intelligent product buckets
    # ═══════════════════════════════════════════════════════════
    if config.anthropic_api_key:
        print("\n🤖 Step 4: Generating base bucket based on base_prompt...")
        # LLM initialization - creates Anthropic Claude client
        generator = BucketGenerator(config.anthropic_api_key)
        
        # Get user requirements (optional)
        user_requirements = input("\nEnter shopping requirements (press ENTER for default): ").strip()
        if not user_requirements:
            user_requirements = "Buy healthy ingredients for a week, including meat, vegetables, fruits, and essentials"
        
        # LLM API call - uses Claude to categorize products intelligently
        buckets = generator.generate_buckets(
            products=products,
            user_requirements=user_requirements,
            recent_history=recent_lists
        )
        
        print("\n" + generator.format_buckets(buckets))
        
        # Save shopping list
        all_items = []
        for bucket_items in buckets.values():
            all_items.extend(bucket_items)
        
        save = input("\nSave this shopping list to history? (y/n): ").strip().lower()
        if save == 'y':
            history.add_shopping_list(all_items, notes=user_requirements)
        
        # 5. Add to cart (optional)
        add_to_cart = input("\nAdd products to cart? (y/n): ").strip().lower()
        if add_to_cart == 'y':
            print("\n🛒 Step 5: Adding products to cart...")
            with CartAutomation() as cart:
                result = cart.add_from_buckets(buckets)
                if result.success:
                    cart.view_cart()
                    print("\n💡 Browser will remain open, you can view the cart and continue shopping")
    else:
        print("\n⚠️ Skipping bucket generation (ANTHROPIC_API_KEY required)")
    
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
