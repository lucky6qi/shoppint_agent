"""Generate base bucket based on base_prompt"""
import anthropic
from typing import List, Dict, Any, Optional
import json


class BucketGenerator:
    """Generate shopping list bucket classification based on prompts"""
    
    def __init__(self, api_key: str):
        # ═══════════════════════════════════════════════════════════
        # 🔴 LLM INITIALIZATION - Anthropic Claude API
        # ═══════════════════════════════════════════════════════════
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # ═══════════════════════════════════════════════════════════
        # 🔴 LLM PROMPT - Base prompt for product categorization
        # ═══════════════════════════════════════════════════════════
        self.base_prompt = """You are an intelligent shopping assistant. Please categorize products into different buckets based on user shopping requirements.

Bucket classification rules:
1. Essentials (essentials) - Daily essential basic products, such as milk, eggs, bread, etc.
2. Meat (meat) - Various meats and proteins
3. Vegetables (vegetables) - Fresh vegetables
4. Fruit (fruit) - Fresh fruits
5. Snacks (snacks) - Snacks, sweets, etc.
6. Beverages (beverages) - Various drinks
7. Other (other) - Other products

Please generate reasonable product lists for each bucket based on user requirements and discount product information."""
    
    def generate_buckets(self, products: List[Dict[str, Any]], 
                        user_requirements: str = "",
                        recent_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Generate base bucket"""
        
        # Prepare product list
        products_text = "\n".join([
            f"- {p['title']} | {p['price']} | Discount: {p.get('discount', 0)}%"
            for p in products[:100]  # Limit quantity for efficiency
        ])
        
        # Prepare history
        history_text = ""
        if recent_history:
            history_text = "\nRecent shopping history:\n"
            for hist in recent_history[:3]:  # Only take last 3
                items = hist.get("items", [])
                history_text += f"- Purchased {len(items)} items\n"
        
        # Build complete prompt
        prompt = f"""{self.base_prompt}

Available discount products:
{products_text}

{history_text}

User requirements:
{user_requirements or "Buy healthy ingredients for a week, including meat, vegetables, fruits, and essentials"}

Please select appropriate products for each bucket, maximum 10 products per bucket. Return JSON format:
{{
  "essentials": [{{"title": "Product name", "price": "Price", "reason": "Selection reason"}}],
  "meat": [...],
  "vegetables": [...],
  "fruit": [...],
  "snacks": [...],
  "beverages": [...],
  "other": [...]
}}"""
        
        try:
            # ═══════════════════════════════════════════════════════════
            # 🔴 LLM API CALL - Claude 3.5 Sonnet
            # ═══════════════════════════════════════════════════════════
            # This is where the LLM is called to generate intelligent bucket classification
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # LLM Model
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt  # LLM Prompt with products, history, and requirements
                }]
            )
            
            # Parse response
            response_text = message.content[0].text
            # Try to extract JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                buckets = json.loads(json_str)
                
                # Convert to product dictionary format
                result = {}
                for bucket_name, items in buckets.items():
                    result[bucket_name] = []
                    for item in items:
                        # Find complete information from products
                        product = self._find_product(products, item.get("title", ""))
                        if product:
                            result[bucket_name].append({
                                **product,
                                "reason": item.get("reason", "")
                            })
                
                return result
            else:
                print("⚠️ Unable to parse AI response as JSON format")
                return self._create_default_buckets(products)
                
        except Exception as e:
            print(f"❌ Failed to generate bucket: {e}")
            return self._create_default_buckets(products)
    
    def _find_product(self, products: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """Find matching product in product list"""
        title_lower = title.lower()
        for product in products:
            if title_lower in product["title"].lower() or product["title"].lower() in title_lower:
                return product
        return None
    
    def _create_default_buckets(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create default bucket classification"""
        buckets = {
            "essentials": [],
            "meat": [],
            "vegetables": [],
            "fruit": [],
            "snacks": [],
            "beverages": [],
            "other": []
        }
        
        # Simple keyword classification
        keywords = {
            "essentials": ["melk", "milk", "eieren", "eggs", "brood", "bread", "boter", "butter"],
            "meat": ["vlees", "meat", "kip", "chicken", "vis", "fish", "gehakt"],
            "vegetables": ["groente", "vegetable", "tomaat", "tomato", "ui", "onion", "wortel"],
            "fruit": ["fruit", "appel", "apple", "banaan", "banana", "sinaasappel"],
            "snacks": ["snack", "chips", "koek", "snoep", "chocolate"],
            "beverages": ["drank", "drink", "sap", "juice", "water", "cola"]
        }
        
        for product in products:
            title_lower = product["title"].lower()
            categorized = False
            
            for bucket, kw_list in keywords.items():
                if any(kw in title_lower for kw in kw_list):
                    if len(buckets[bucket]) < 10:
                        buckets[bucket].append(product)
                        categorized = True
                        break
            
            if not categorized and len(buckets["other"]) < 10:
                buckets["other"].append(product)
        
        return buckets
    
    def format_buckets(self, buckets: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format bucket output"""
        result = "🛒 Shopping List Classification (Base Buckets)\n"
        result += "=" * 50 + "\n\n"
        
        bucket_names = {
            "essentials": "Essentials",
            "meat": "Meat",
            "vegetables": "Vegetables",
            "fruit": "Fruit",
            "snacks": "Snacks",
            "beverages": "Beverages",
            "other": "Other"
        }
        
        for bucket_name, items in buckets.items():
            display_name = bucket_names.get(bucket_name, bucket_name)
            result += f"📦 {display_name} ({len(items)} items):\n"
            
            for item in items:
                result += f"   - {item['title']} | {item['price']}\n"
                if item.get("reason"):
                    result += f"     Reason: {item['reason']}\n"
            
            result += "\n"
        
        return result
