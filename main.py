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
        
        # Get user prompt (can be from file or direct input)
        prompt_file = "prompts/default_prompt.txt"
        user_prompt = ""
        
        # Try to load from file first
        if os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    user_prompt = f.read().strip()
                print(f"\n📝 Loaded prompt from {prompt_file}")
                print(f"Prompt content:\n{user_prompt}\n")
            except Exception as e:
                print(f"⚠️ Failed to load prompt file: {e}")
        
        # If no file or file is empty, ask for input
        if not user_prompt:
            print("\nEnter shopping prompt (or press ENTER for default):")
            print("You can include:")
            print("  - Shopping Requirements: ...")
            print("  - Must-buy Items: ...")
            print("Or just type your requirements directly")
            user_input = input("> ").strip()
            if user_input:
                user_prompt = user_input
            else:
                # Default prompt
                user_prompt = """Shopping Requirements:
Buy healthy ingredients for a week, including meat, vegetables, fruits, and essentials.

Must-buy Items:
"""
        
        # LLM API call - uses Claude to categorize products intelligently
        buckets = generator.generate_buckets(
            products=products,
            user_prompt=user_prompt,
            recent_history=recent_lists
        )
        
        print("\n" + generator.format_buckets(buckets))
        
        # 5. Add to cart directly
        print("\n🛒 Step 5: Adding products to cart...")
        cart = CartAutomation()
        try:
            result = cart.add_from_buckets(buckets)
            if result.success:
                cart.view_cart()
                print("\n💡 Browser will remain open for you to login and checkout")
                print("   Please manually close the browser when done")
                
                # Delete cache file completely after adding to cart
                scraper.delete_cache()
                
                # Wait for user to finish (keep browser open)
                input("\nPress ENTER after you've finished checkout to exit...")
        finally:
            # Only close if user pressed ENTER
            cart.close()
    else:
        print("\n⚠️ Skipping bucket generation (ANTHROPIC_API_KEY required)")
    
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
