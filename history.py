"""Shopping history management - Local JSON database"""
import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict
import uuid


class ShoppingHistoryDB:
    """Shopping history database with indexing and query support"""
    
    def __init__(self, db_file: str = "shopping_history.json"):
        self.db_file = db_file
        self.db = self._load_db()
        self._build_indexes()
    
    def _load_db(self) -> Dict[str, Any]:
        """Load database"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Migrate from old format to new format
                    if isinstance(data, list):
                        return self._migrate_from_list(data)
                    return data
            except Exception as e:
                print(f"⚠️ Failed to load database: {e}, creating new database")
                return self._create_empty_db()
        return self._create_empty_db()
    
    def _create_empty_db(self) -> Dict[str, Any]:
        """Create empty database structure"""
        return {
            "version": "1.0",
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            "lists": [],
            "indexes": {
                "by_date": {},
                "by_product": {},
                "by_category": {}
            }
        }
    
    def _migrate_from_list(self, old_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Migrate data from old format"""
        db = self._create_empty_db()
        for item in old_data:
            db["lists"].append({
                "id": str(uuid.uuid4()),
                "date": item.get("date", datetime.now().isoformat()),
                "items": item.get("items", []),
                "notes": item.get("notes", ""),
                "total_items": item.get("total_items", len(item.get("items", [])))
            })
        db["metadata"]["created_at"] = datetime.now().isoformat()
        return db
    
    def _save_db(self):
        """Save database"""
        try:
            self.db["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Failed to save database: {e}")
    
    def _build_indexes(self):
        """Build indexes"""
        indexes = {
            "by_date": defaultdict(list),
            "by_product": defaultdict(list),
            "by_category": defaultdict(list)
        }
        
        for shopping_list in self.db.get("lists", []):
            list_id = shopping_list.get("id")
            date_str = shopping_list.get("date", "")[:10]  # YYYY-MM-DD
            
            # Date index
            indexes["by_date"][date_str].append(list_id)
            
            # Product index
            for item in shopping_list.get("items", []):
                title = item.get("title", "").lower()
                if title:
                    indexes["by_product"][title].append(list_id)
            
            # Category index (if category field exists)
            for item in shopping_list.get("items", []):
                category = item.get("category", "other")
                indexes["by_category"][category].append(list_id)
        
        self.db["indexes"] = {
            "by_date": {k: list(set(v)) for k, v in indexes["by_date"].items()},
            "by_product": {k: list(set(v)) for k, v in indexes["by_product"].items()},
            "by_category": {k: list(set(v)) for k, v in indexes["by_category"].items()}
        }
    
    def add_shopping_list(self, items: List[Dict[str, Any]], 
                         notes: str = "", list_id: Optional[str] = None) -> str:
        """Add new shopping list"""
        if list_id is None:
            list_id = str(uuid.uuid4())
        
        shopping_list = {
            "id": list_id,
            "date": datetime.now().isoformat(),
            "items": items,
            "notes": notes,
            "total_items": len(items)
        }
        
        self.db["lists"].append(shopping_list)
        self._build_indexes()
        self._save_db()
        
        print(f"✅ Shopping list saved (ID: {list_id[:8]}..., {len(items)} items)")
        return list_id
    
    def get_list_by_id(self, list_id: str) -> Optional[Dict[str, Any]]:
        """Get shopping list by ID"""
        for shopping_list in self.db.get("lists", []):
            if shopping_list.get("id") == list_id:
                return shopping_list
        return None
    
    def get_recent_lists(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent N shopping lists"""
        lists = sorted(
            self.db.get("lists", []),
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        return lists[:count]
    
    def get_latest_list(self) -> Optional[Dict[str, Any]]:
        """Get latest shopping list"""
        recent = self.get_recent_lists(1)
        return recent[0] if recent else None
    
    def query_by_date(self, date_str: Optional[str] = None, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query by date
        
        Args:
            date_str: Exact date (YYYY-MM-DD)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        results = []
        
        if date_str:
            # Exact date query
            list_ids = self.db["indexes"]["by_date"].get(date_str, [])
            results = [self.get_list_by_id(id) for id in list_ids if self.get_list_by_id(id)]
        elif start_date or end_date:
            # Date range query
            for shopping_list in self.db.get("lists", []):
                list_date = shopping_list.get("date", "")[:10]
                if start_date and list_date < start_date:
                    continue
                if end_date and list_date > end_date:
                    continue
                results.append(shopping_list)
        else:
            # Return all
            results = self.db.get("lists", [])
        
        return sorted(results, key=lambda x: x.get("date", ""), reverse=True)
    
    def query_by_product(self, product_name: str, 
                        case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Query by product name"""
        if not case_sensitive:
            product_name = product_name.lower()
        
        # Use index to find
        list_ids = set()
        for key, ids in self.db["indexes"]["by_product"].items():
            if product_name in key or key in product_name:
                list_ids.update(ids)
        
        # Get complete shopping lists
        results = []
        for list_id in list_ids:
            shopping_list = self.get_list_by_id(list_id)
            if shopping_list:
                results.append(shopping_list)
        
        return sorted(results, key=lambda x: x.get("date", ""), reverse=True)
    
    def query_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Query by category"""
        list_ids = self.db["indexes"]["by_category"].get(category.lower(), [])
        results = [self.get_list_by_id(id) for id in list_ids if self.get_list_by_id(id)]
        return sorted(results, key=lambda x: x.get("date", ""), reverse=True)
    
    def query_by_notes(self, keyword: str) -> List[Dict[str, Any]]:
        """Query by notes keyword"""
        results = []
        keyword_lower = keyword.lower()
        
        for shopping_list in self.db.get("lists", []):
            notes = shopping_list.get("notes", "").lower()
            if keyword_lower in notes:
                results.append(shopping_list)
        
        return sorted(results, key=lambda x: x.get("date", ""), reverse=True)
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Comprehensive search (product name, notes, category)"""
        results = []
        query_lower = query.lower()
        
        for shopping_list in self.db.get("lists", []):
            # Search product names
            for item in shopping_list.get("items", []):
                if query_lower in item.get("title", "").lower():
                    results.append(shopping_list)
                    break
            
            # Search notes
            if query_lower in shopping_list.get("notes", "").lower():
                if shopping_list not in results:
                    results.append(shopping_list)
            
            # Search categories
            for item in shopping_list.get("items", []):
                if query_lower in item.get("category", "").lower():
                    if shopping_list not in results:
                        results.append(shopping_list)
                    break
        
        return sorted(results, key=lambda x: x.get("date", ""), reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics"""
        lists = self.db.get("lists", [])
        total_lists = len(lists)
        total_items = sum(len(lst.get("items", [])) for lst in lists)
        
        # Most frequently purchased products
        product_counts = defaultdict(int)
        for shopping_list in lists:
            for item in shopping_list.get("items", []):
                title = item.get("title", "").lower()
                if title:
                    product_counts[title] += 1
        
        top_products = sorted(
            product_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Date range
        dates = [lst.get("date", "")[:10] for lst in lists if lst.get("date")]
        date_range = {}
        if dates:
            dates_sorted = sorted(dates)
            date_range = {
                "first": dates_sorted[0],
                "last": dates_sorted[-1]
            }
        
        return {
            "total_lists": total_lists,
            "total_items": total_items,
            "average_items_per_list": round(total_items / total_lists, 2) if total_lists > 0 else 0,
            "top_products": [{"name": name, "count": count} for name, count in top_products],
            "date_range": date_range
        }
    
    def format_recent_lists(self, count: int = 10) -> str:
        """Format recent N shopping lists as string"""
        recent = self.get_recent_lists(count)
        
        if not recent:
            return "No shopping history records"
        
        result = f"📋 Recent {len(recent)} Shopping Lists\n"
        result += "=" * 50 + "\n\n"
        
        for i, shopping_list in enumerate(recent, 1):
            date_str = shopping_list.get("date", "Unknown date")
            items = shopping_list.get("items", [])
            notes = shopping_list.get("notes", "")
            list_id = shopping_list.get("id", "")[:8]
            
            result += f"📅 Shopping #{i} ({date_str[:10]}) [ID: {list_id}...]\n"
            result += f"   Items: {len(items)}\n"
            
            if notes:
                result += f"   Notes: {notes}\n"
            
            result += "   Product list:\n"
            for item in items[:10]:  # Only show first 10
                title = item.get("title", "Unknown product")
                price = item.get("price", "Unknown price")
                result += f"     - {title} ({price})\n"
            
            if len(items) > 10:
                result += f"     ... {len(items) - 10} more items\n"
            
            result += "\n"
        
        return result
    
    def delete_list(self, list_id: str) -> bool:
        """Delete shopping list"""
        lists = self.db.get("lists", [])
        original_count = len(lists)
        
        self.db["lists"] = [lst for lst in lists if lst.get("id") != list_id]
        
        if len(self.db["lists"]) < original_count:
            self._build_indexes()
            self._save_db()
            print(f"✅ Shopping list deleted (ID: {list_id[:8]}...)")
            return True
        
        print(f"❌ Shopping list not found (ID: {list_id[:8]}...)")
        return False
    
    def update_list(self, list_id: str, items: Optional[List[Dict[str, Any]]] = None,
                   notes: Optional[str] = None) -> bool:
        """Update shopping list"""
        shopping_list = self.get_list_by_id(list_id)
        if not shopping_list:
            print(f"❌ Shopping list not found (ID: {list_id[:8]}...)")
            return False
        
        if items is not None:
            shopping_list["items"] = items
            shopping_list["total_items"] = len(items)
        
        if notes is not None:
            shopping_list["notes"] = notes
        
        shopping_list["date"] = datetime.now().isoformat()
        
        self._build_indexes()
        self._save_db()
        print(f"✅ Shopping list updated (ID: {list_id[:8]}...)")
        return True


# Backward compatibility alias
ShoppingHistory = ShoppingHistoryDB
