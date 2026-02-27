import tempfile
"""
Custom Category Builder
Allows users to create personal categories like "Wedding Fund Expenses"
or "Side Business Costs" with auto-tagging rules.
"""

import json
import os
import re
import tempfile
_TMPDIR = tempfile.gettempdir()
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum


class RuleType(str, Enum):
    KEYWORD = "keyword"          # Description contains keyword
    MERCHANT = "merchant"        # Specific merchant name
    AMOUNT_RANGE = "amount_range"  # Amount within range
    AMOUNT_ABOVE = "amount_above"  # Amount > threshold
    AMOUNT_BELOW = "amount_below"  # Amount < threshold
    REGEX = "regex"              # Regex pattern on description
    DAY_OF_WEEK = "day_of_week"  # Specific day (for recurring patterns)
    ORIGINAL_CATEGORY = "original_category"  # Override existing category


@dataclass
class TagRule:
    rule_id: str
    rule_type: RuleType
    value: Any              # keyword string, merchant name, (min,max), regex pattern etc.
    priority: int = 5       # 1=highest, 10=lowest
    is_exclusive: bool = False  # If True, don't apply other rules after this

@dataclass
class CustomCategory:
    category_id: str
    name: str                   # e.g., "Wedding Fund Expenses"
    description: str            # User-provided description
    color: str                  # Hex color code for UI
    icon: str                   # Emoji or icon name
    rules: List[TagRule]
    created_at: str
    updated_at: str
    is_active: bool = True
    budget_limit: Optional[float] = None   # Monthly budget
    parent_category: Optional[str] = None  # Link to standard category for reports
    tags: List[str] = field(default_factory=list)  # Auto-applied tags

    def to_dict(self):
        return asdict(self)


class CustomCategoryBuilder:
    """
    Manages user-defined categories and their auto-tagging rules.
    Persists to JSON (upgradeable to SQLite for production).
    """
    
    def __init__(self, store_path: str = os.path.join(_TMPDIR, "custom_categories.json")):
        self.store_path = store_path
        self.categories: Dict[str, CustomCategory] = {}
        self._load()
        
        # Seed example categories if empty
        if not self.categories:
            self._seed_examples()
    
    def _load(self):
        if os.path.exists(self.store_path):
            with open(self.store_path) as f:
                data = json.load(f)
                for cat_id, cat_data in data.items():
                    rules = [
                        TagRule(
                            rule_id=r["rule_id"],
                            rule_type=RuleType(r["rule_type"]),
                            value=r["value"],
                            priority=r.get("priority", 5),
                            is_exclusive=r.get("is_exclusive", False)
                        )
                        for r in cat_data.get("rules", [])
                    ]
                    cat_data["rules"] = rules
                    self.categories[cat_id] = CustomCategory(**cat_data)
    
    def _save(self):
        data = {}
        for cat_id, cat in self.categories.items():
            cat_dict = cat.to_dict()
            cat_dict["rules"] = [
                {
                    "rule_id": r["rule_id"],
                    "rule_type": r["rule_type"],
                    "value": r["value"],
                    "priority": r["priority"],
                    "is_exclusive": r["is_exclusive"]
                }
                for r in cat_dict["rules"]
            ]
            data[cat_id] = cat_dict
        
        try:
            save_dir = os.path.dirname(self.store_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"  WARN: Custom categories save skipped ({e}). Active in-memory only.")
    
    def _seed_examples(self):
        """Create example custom categories for demo."""
        self.create_category(
            name="Wedding Fund Expenses",
            description="All expenses related to my wedding planning",
            color="#FF69B4",
            icon="💍",
            rules=[
                {"type": RuleType.KEYWORD, "value": "wedding"},
                {"type": RuleType.KEYWORD, "value": "mehendi"},
                {"type": RuleType.KEYWORD, "value": "baraat"},
                {"type": RuleType.KEYWORD, "value": "catering"},
                {"type": RuleType.KEYWORD, "value": "decoration"},
                {"type": RuleType.KEYWORD, "value": "photographer"},
                {"type": RuleType.KEYWORD, "value": "invitation cards"},
                {"type": RuleType.KEYWORD, "value": "shaadi"},
                {"type": RuleType.KEYWORD, "value": "vivah"},
                {"type": RuleType.MERCHANT, "value": "WeddingWire"},
                {"type": RuleType.MERCHANT, "value": "Shaadi.com"},
            ],
            budget_limit=500000.0,
            tags=["wedding", "one-time-event"]
        )
        
        self.create_category(
            name="Side Business Costs",
            description="Expenses for my freelance / side business",
            color="#4CAF50",
            icon="💼",
            rules=[
                {"type": RuleType.KEYWORD, "value": "freelance"},
                {"type": RuleType.KEYWORD, "value": "client"},
                {"type": RuleType.KEYWORD, "value": "invoice"},
                {"type": RuleType.KEYWORD, "value": "hosting"},
                {"type": RuleType.KEYWORD, "value": "domain"},
                {"type": RuleType.KEYWORD, "value": "aws"},
                {"type": RuleType.KEYWORD, "value": "digital ocean"},
                {"type": RuleType.KEYWORD, "value": "gsuite"},
                {"type": RuleType.KEYWORD, "value": "figma"},
                {"type": RuleType.KEYWORD, "value": "notion"},
                {"type": RuleType.MERCHANT, "value": "GoDaddy"},
                {"type": RuleType.MERCHANT, "value": "Hostinger"},
            ],
            budget_limit=None,
            tags=["business", "tax-deductible"]
        )
        
        self.create_category(
            name="Baby & Kids",
            description="Expenses for baby and children",
            color="#87CEEB",
            icon="🍼",
            rules=[
                {"type": RuleType.KEYWORD, "value": "baby"},
                {"type": RuleType.KEYWORD, "value": "diapers"},
                {"type": RuleType.KEYWORD, "value": "pampers"},
                {"type": RuleType.KEYWORD, "value": "huggies"},
                {"type": RuleType.KEYWORD, "value": "firstcry"},
                {"type": RuleType.KEYWORD, "value": "school bag"},
                {"type": RuleType.KEYWORD, "value": "uniform"},
                {"type": RuleType.KEYWORD, "value": "toys"},
                {"type": RuleType.MERCHANT, "value": "FirstCry"},
            ],
            tags=["family", "kids"]
        )
    
    def create_category(self, name: str, description: str, color: str,
                        icon: str, rules: List[dict],
                        budget_limit: Optional[float] = None,
                        tags: Optional[List[str]] = None,
                        parent_category: Optional[str] = None) -> CustomCategory:
        """Create a new custom category with rules."""
        
        cat_id = re.sub(r'[^a-z0-9]', '_', name.lower())[:30]
        now = datetime.now().isoformat()
        
        tag_rules = []
        for i, rule in enumerate(rules):
            tag_rules.append(TagRule(
                rule_id=f"{cat_id}_rule_{i}",
                rule_type=rule["type"],
                value=rule["value"],
                priority=rule.get("priority", 5),
                is_exclusive=rule.get("is_exclusive", False)
            ))
        
        cat = CustomCategory(
            category_id=cat_id,
            name=name,
            description=description,
            color=color,
            icon=icon,
            rules=tag_rules,
            created_at=now,
            updated_at=now,
            is_active=True,
            budget_limit=budget_limit,
            parent_category=parent_category,
            tags=tags or []
        )
        
        self.categories[cat_id] = cat
        self._save()
        return cat
    
    def add_rule(self, category_id: str, rule_type: RuleType, value: Any,
                  priority: int = 5) -> bool:
        """Add a new rule to an existing category."""
        if category_id not in self.categories:
            return False
        
        cat = self.categories[category_id]
        rule_id = f"{category_id}_rule_{len(cat.rules)}"
        cat.rules.append(TagRule(rule_id, rule_type, value, priority))
        cat.updated_at = datetime.now().isoformat()
        self._save()
        return True
    
    def match_transaction(self, description: str, amount: float,
                           date: Optional[str] = None,
                           merchant_name: Optional[str] = None,
                           original_category: Optional[str] = None
                           ) -> Optional[CustomCategory]:
        """
        Check if a transaction matches any custom category.
        Returns the highest-priority matching CustomCategory or None.
        """
        desc_lower = description.lower()
        matches = []
        
        for cat_id, cat in self.categories.items():
            if not cat.is_active:
                continue
            
            score = 0
            matched_rules = 0
            
            for rule in sorted(cat.rules, key=lambda r: r.priority):
                rule_matched = False
                
                if rule.rule_type == RuleType.KEYWORD:
                    rule_matched = rule.value.lower() in desc_lower
                
                elif rule.rule_type == RuleType.MERCHANT:
                    if merchant_name:
                        rule_matched = rule.value.lower() in merchant_name.lower()
                
                elif rule.rule_type == RuleType.AMOUNT_RANGE:
                    min_amt, max_amt = rule.value
                    rule_matched = min_amt <= amount <= max_amt
                
                elif rule.rule_type == RuleType.AMOUNT_ABOVE:
                    rule_matched = amount > rule.value
                
                elif rule.rule_type == RuleType.AMOUNT_BELOW:
                    rule_matched = amount < rule.value
                
                elif rule.rule_type == RuleType.REGEX:
                    rule_matched = bool(re.search(rule.value, desc_lower, re.I))
                
                elif rule.rule_type == RuleType.ORIGINAL_CATEGORY:
                    if original_category:
                        rule_matched = rule.value.lower() in original_category.lower()
                
                if rule_matched:
                    matched_rules += 1
                    score += (11 - rule.priority)  # higher priority = higher score
                    if rule.is_exclusive:
                        break
            
            if matched_rules > 0:
                matches.append((score, cat))
        
        if not matches:
            return None
        
        # Return highest scoring match
        matches.sort(key=lambda x: x[0], reverse=True)
        return matches[0][1]
    
    def get_all_categories(self) -> List[dict]:
        return [
            {
                "category_id": cat.category_id,
                "name": cat.name,
                "icon": cat.icon,
                "color": cat.color,
                "description": cat.description,
                "rules_count": len(cat.rules),
                "budget_limit": cat.budget_limit,
                "tags": cat.tags,
                "is_active": cat.is_active
            }
            for cat in self.categories.values()
        ]
    
    def delete_category(self, category_id: str) -> bool:
        if category_id not in self.categories:
            return False
        del self.categories[category_id]
        self._save()
        return True
    
    def update_budget(self, category_id: str, budget: float) -> bool:
        if category_id not in self.categories:
            return False
        self.categories[category_id].budget_limit = budget
        self.categories[category_id].updated_at = datetime.now().isoformat()
        self._save()
        return True