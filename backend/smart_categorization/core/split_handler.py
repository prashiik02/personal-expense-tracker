"""
Split Transaction Handler
Splits a single transaction (e.g., Amazon order) into multiple sub-category items
using NLP on the transaction description / line items.
"""

import re
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

@dataclass
class SplitItem:
    description: str
    amount: float
    category: str
    subcategory: str
    percentage: float  # fraction of total bill

@dataclass
class SplitResult:
    original_description: str
    original_amount: float
    was_split: bool
    split_items: List[SplitItem]
    split_method: str  # "keyword_heuristic" | "nlp_line_items" | "llm_assisted"

# ─────────────────────────────────────────────
# KEYWORD → CATEGORY MAPPING FOR SPLIT
# ─────────────────────────────────────────────

SPLIT_KEYWORD_MAP = {
    # Electronics
    "mobile": ("Shopping", "Electronics"),
    "laptop": ("Shopping", "Electronics"),
    "tablet": ("Shopping", "Electronics"),
    "earphones": ("Shopping", "Electronics"),
    "headphones": ("Shopping", "Electronics"),
    "charger": ("Shopping", "Electronics"),
    "cable usb": ("Shopping", "Electronics"),
    "keyboard": ("Shopping", "Electronics"),
    "mouse": ("Shopping", "Electronics"),
    "monitor": ("Shopping", "Electronics"),
    "camera": ("Shopping", "Electronics"),
    "smartwatch": ("Shopping", "Electronics"),
    "tv television": ("Shopping", "Electronics"),
    "speaker": ("Shopping", "Electronics"),
    "router wifi": ("Shopping", "Electronics"),
    
    # Clothing
    "shirt": ("Shopping", "Clothing & Apparel"),
    "t-shirt": ("Shopping", "Clothing & Apparel"),
    "tshirt": ("Shopping", "Clothing & Apparel"),
    "jeans": ("Shopping", "Clothing & Apparel"),
    "kurta": ("Shopping", "Clothing & Apparel"),
    "saree": ("Shopping", "Clothing & Apparel"),
    "dress": ("Shopping", "Clothing & Apparel"),
    "jacket": ("Shopping", "Clothing & Apparel"),
    "hoodie": ("Shopping", "Clothing & Apparel"),
    "leggings": ("Shopping", "Clothing & Apparel"),
    "innerwear": ("Shopping", "Clothing & Apparel"),
    "underwear": ("Shopping", "Clothing & Apparel"),
    "socks": ("Shopping", "Clothing & Apparel"),
    "ethnic wear": ("Shopping", "Clothing & Apparel"),
    
    # Footwear
    "shoes": ("Shopping", "Footwear"),
    "sandals": ("Shopping", "Footwear"),
    "slippers": ("Shopping", "Footwear"),
    "sneakers": ("Shopping", "Footwear"),
    "boots": ("Shopping", "Footwear"),
    "chappal": ("Shopping", "Footwear"),
    
    # Books
    "book": ("Shopping", "Books & Stationery"),
    "novel": ("Shopping", "Books & Stationery"),
    "textbook": ("Shopping", "Books & Stationery"),
    "notebook": ("Shopping", "Books & Stationery"),
    "stationery": ("Shopping", "Books & Stationery"),
    "pen ": ("Shopping", "Books & Stationery"),
    
    # Groceries / Kitchen
    "grocery": ("Food & Dining", "Groceries"),
    "groceries": ("Food & Dining", "Groceries"),
    "vegetables": ("Food & Dining", "Groceries"),
    "fruits": ("Food & Dining", "Groceries"),
    "rice ": ("Food & Dining", "Groceries"),
    "dal ": ("Food & Dining", "Groceries"),
    "flour": ("Food & Dining", "Groceries"),
    "oil ": ("Food & Dining", "Groceries"),
    "spices": ("Food & Dining", "Groceries"),
    "sugar": ("Food & Dining", "Groceries"),
    "salt ": ("Food & Dining", "Groceries"),
    "snacks": ("Food & Dining", "Groceries"),
    "biscuits": ("Food & Dining", "Groceries"),
    "beverages": ("Food & Dining", "Groceries"),
    "baby food": ("Food & Dining", "Groceries"),
    
    # Personal Care / Beauty
    "shampoo": ("Personal Care", "Beauty & Cosmetics"),
    "conditioner": ("Personal Care", "Beauty & Cosmetics"),
    "face wash": ("Personal Care", "Beauty & Cosmetics"),
    "moisturizer": ("Personal Care", "Beauty & Cosmetics"),
    "sunscreen": ("Personal Care", "Beauty & Cosmetics"),
    "lipstick": ("Personal Care", "Beauty & Cosmetics"),
    "foundation": ("Personal Care", "Beauty & Cosmetics"),
    "perfume": ("Personal Care", "Beauty & Cosmetics"),
    "deodorant": ("Personal Care", "Beauty & Cosmetics"),
    "razor": ("Personal Care", "Beauty & Cosmetics"),
    "trimmer": ("Personal Care", "Beauty & Cosmetics"),
    
    # Healthcare
    "medicine": ("Healthcare", "Pharmacy"),
    "tablet ": ("Healthcare", "Pharmacy"),
    "capsule": ("Healthcare", "Pharmacy"),
    "syrup": ("Healthcare", "Pharmacy"),
    "supplement": ("Healthcare", "Pharmacy"),
    "vitamins": ("Healthcare", "Pharmacy"),
    "protein powder": ("Healthcare", "Pharmacy"),
    "first aid": ("Healthcare", "Pharmacy"),
    "mask": ("Healthcare", "Pharmacy"),
    
    # Home & Furniture
    "furniture": ("Home & Maintenance", "Home & Furniture"),
    "sofa": ("Home & Maintenance", "Home & Furniture"),
    "bed ": ("Home & Maintenance", "Home & Furniture"),
    "mattress": ("Home & Maintenance", "Home & Furniture"),
    "chair": ("Home & Maintenance", "Home & Furniture"),
    "table ": ("Home & Maintenance", "Home & Furniture"),
    "lamp": ("Home & Maintenance", "Home & Furniture"),
    "curtains": ("Home & Maintenance", "Home & Furniture"),
    "bedsheet": ("Home & Maintenance", "Home & Furniture"),
    "pillow": ("Home & Maintenance", "Home & Furniture"),
    "storage": ("Home & Maintenance", "Home & Furniture"),
    
    # Kitchen Appliances
    "mixer grinder": ("Shopping", "Electronics"),
    "microwave": ("Shopping", "Electronics"),
    "air fryer": ("Shopping", "Electronics"),
    "pressure cooker": ("Shopping", "Electronics"),
    "water purifier": ("Shopping", "Electronics"),
    
    # Toys & Kids
    "toys": ("Shopping", "Gifts & Toys"),
    "game board": ("Shopping", "Gifts & Toys"),
    "kids": ("Shopping", "Gifts & Toys"),
    
    # Sports
    "sports": ("Shopping", "Sports & Fitness Equipment"),
    "yoga mat": ("Shopping", "Sports & Fitness Equipment"),
    "dumbbell": ("Shopping", "Sports & Fitness Equipment"),
    "cricket bat": ("Shopping", "Sports & Fitness Equipment"),
    "football": ("Shopping", "Sports & Fitness Equipment"),
}

# Merchants known to carry multiple categories
SPLITTABLE_MERCHANTS = {
    "amazon", "flipkart", "meesho", "snapdeal", "jiomart",
    "myntra", "nykaa", "purplle", "firstcry"
}


class SplitTransactionHandler:
    """
    Handles splitting of multi-category transactions.
    """
    
    def __init__(self):
        # Sort keywords by length desc for greedy matching
        self.sorted_keywords = sorted(
            SPLIT_KEYWORD_MAP.keys(), key=len, reverse=True)
    
    def should_split(self, description: str, merchant_name: Optional[str] = None) -> bool:
        """Determine if this transaction could be a split candidate."""
        desc_lower = description.lower()
        
        # Check if it's from a known multi-category merchant
        if merchant_name and merchant_name.lower() in SPLITTABLE_MERCHANTS:
            return True
        
        # Check if description contains multiple category keywords
        matched_cats = set()
        for kw in self.sorted_keywords:
            if kw.strip() in desc_lower:
                cat = SPLIT_KEYWORD_MAP[kw][0]
                matched_cats.add(cat)
        
        return len(matched_cats) >= 2
    
    def split(self, description: str, amount: float,
              line_items: Optional[List[dict]] = None) -> SplitResult:
        """
        Split a transaction into categorized sub-items.
        
        Args:
            description: Transaction description
            amount: Total transaction amount
            line_items: Optional list of {"name": ..., "amount": ...} dicts
                        (e.g., from parsed order email/SMS)
        """
        
        # If we have explicit line items, use them directly
        if line_items:
            return self._split_from_line_items(description, amount, line_items)
        
        # Otherwise use keyword heuristic on description
        return self._split_from_description(description, amount)
    
    def _split_from_line_items(self, description: str, amount: float,
                                line_items: List[dict]) -> SplitResult:
        """Split using explicit line item data."""
        items = []
        total_assigned = 0
        
        for item in line_items:
            item_name = item.get("name", "").lower()
            item_amount = float(item.get("amount", 0))
            
            # Find best matching category for this item
            cat, subcat = self._match_keyword(item_name)
            pct = (item_amount / amount) if amount > 0 else 0
            
            items.append(SplitItem(
                description=item.get("name", item_name),
                amount=item_amount,
                category=cat,
                subcategory=subcat,
                percentage=round(pct, 4)
            ))
            total_assigned += item_amount
        
        # Handle rounding residual
        if items and abs(total_assigned - amount) > 0.5:
            items[-1].amount += (amount - total_assigned)
        
        return SplitResult(
            original_description=description,
            original_amount=amount,
            was_split=len(items) > 1,
            split_items=items,
            split_method="nlp_line_items"
        )
    
    def _split_from_description(self, description: str, amount: float) -> SplitResult:
        """Keyword heuristic split when no line items available."""
        desc_lower = description.lower()
        matched = {}  # keyword → (cat, subcat)
        
        for kw in self.sorted_keywords:
            if kw.strip() in desc_lower:
                cat_key = SPLIT_KEYWORD_MAP[kw][0]
                if cat_key not in matched:
                    matched[kw] = SPLIT_KEYWORD_MAP[kw]
        
        if not matched:
            # No keywords found → single item, no split
            return SplitResult(
                original_description=description,
                original_amount=amount,
                was_split=False,
                split_items=[SplitItem(description, amount, "Shopping", "Electronics", 1.0)],
                split_method="keyword_heuristic"
            )
        
        # Distribute amount equally among matched categories
        # In production: use ML to estimate proportional split
        n = len(matched)
        per_item = round(amount / n, 2)
        items = []
        running_total = 0
        
        for i, (kw, (cat, subcat)) in enumerate(matched.items()):
            if i == n - 1:
                item_amt = round(amount - running_total, 2)
            else:
                item_amt = per_item
            running_total += item_amt
            
            items.append(SplitItem(
                description=kw.strip().title(),
                amount=item_amt,
                category=cat,
                subcategory=subcat,
                percentage=round(item_amt / amount, 4) if amount > 0 else 0
            ))
        
        return SplitResult(
            original_description=description,
            original_amount=amount,
            was_split=True,
            split_items=items,
            split_method="keyword_heuristic"
        )
    
    def _match_keyword(self, text: str) -> Tuple[str, str]:
        """Find best category match for a text string."""
        text_lower = text.lower()
        for kw in self.sorted_keywords:
            if kw.strip() in text_lower:
                return SPLIT_KEYWORD_MAP[kw]
        return ("Shopping", "Electronics")  # default
    
    def to_dict(self, result: SplitResult) -> dict:
        return {
            "original_description": result.original_description,
            "original_amount": result.original_amount,
            "was_split": result.was_split,
            "split_method": result.split_method,
            "items": [
                {
                    "description": item.description,
                    "amount": item.amount,
                    "category": item.category,
                    "subcategory": item.subcategory,
                    "percentage": item.percentage
                }
                for item in result.split_items
            ]
        }