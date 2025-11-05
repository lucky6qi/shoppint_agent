"""Shopping list query examples"""
from history import ShoppingHistoryDB


def example_queries():
    """Demonstrate various query functions"""
    db = ShoppingHistoryDB()
    
    print("=" * 60)
    print("📊 Shopping List Database Query Examples")
    print("=" * 60)
    
    # 1. Get statistics
    print("\n1️⃣ Database Statistics:")
    stats = db.get_statistics()
    print(f"   Total shopping lists: {stats['total_lists']}")
    print(f"   Total items: {stats['total_items']}")
    print(f"   Average items per list: {stats['average_items_per_list']}")
    
    if stats['date_range']:
        print(f"   Date range: {stats['date_range']['first']} to {stats['date_range']['last']}")
    
    if stats['top_products']:
        print("\n   Most frequently purchased products:")
        for i, product in enumerate(stats['top_products'][:5], 1):
            print(f"     {i}. {product['name']} - Purchased {product['count']} times")
    
    # 2. Query by date
    print("\n2️⃣ Query by Date:")
    recent_lists = db.get_recent_lists(5)
    if recent_lists:
        first_date = recent_lists[-1].get("date", "")[:10]
        print(f"   Query date: {first_date}")
        results = db.query_by_date(date_str=first_date)
        print(f"   Found {len(results)} shopping lists")
    
    # 3. Query by product name
    print("\n3️⃣ Query by Product Name:")
    if recent_lists:
        # Get a product name from the most recent shopping list
        sample_items = recent_lists[0].get("items", [])
        if sample_items:
            sample_product = sample_items[0].get("title", "")
            if sample_product:
                print(f"   Query product: {sample_product}")
                results = db.query_by_product(sample_product)
                print(f"   Found {len(results)} shopping lists containing this product")
                for result in results[:3]:
                    date_str = result.get("date", "")[:10]
                    print(f"     - {date_str}: {result.get('total_items')} items")
    
    # 4. Query by category
    print("\n4️⃣ Query by Category:")
    categories = ["meat", "vegetables", "fruit", "essentials"]
    for category in categories:
        results = db.query_by_category(category)
        if results:
            print(f"   {category}: {len(results)} shopping lists")
    
    # 5. Comprehensive search
    print("\n5️⃣ Comprehensive Search:")
    search_terms = ["melk", "kip", "fruit"]
    for term in search_terms:
        results = db.search(term)
        if results:
            print(f"   Search '{term}': Found {len(results)} results")
    
    # 6. Query by notes
    print("\n6️⃣ Query by Notes:")
    results = db.query_by_notes("test")
    if results:
        print(f"   Found {len(results)} shopping lists containing 'test'")
    
    # 7. Date range query
    print("\n7️⃣ Date Range Query:")
    if recent_lists:
        dates = [lst.get("date", "")[:10] for lst in recent_lists if lst.get("date")]
        if len(dates) >= 2:
            start_date = sorted(dates)[0]
            end_date = sorted(dates)[-1]
            print(f"   Query range: {start_date} to {end_date}")
            results = db.query_by_date(start_date=start_date, end_date=end_date)
            print(f"   Found {len(results)} shopping lists")


if __name__ == "__main__":
    example_queries()
