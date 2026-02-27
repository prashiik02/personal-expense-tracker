"""
Smart Categorization Pipeline
Orchestrates all 5 components into a single unified pipeline:
1. India Merchant Dictionary
2. ML Categorization + User Feedback Learning
3. Split Transaction Handling
4. Custom Category Builder
5. Merchant Enrichment
"""

import json
import os
import tempfile

_TMPDIR = tempfile.gettempdir()

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Transaction:
    """Input transaction from bank statement / payment app."""
    transaction_id: str
    date: str                         # "YYYY-MM-DD"
    description: str                  # Raw description from bank/UPI
    amount: float                     # Positive = debit, Negative = credit
    currency: str = "INR"
    line_items: Optional[List[dict]] = None  # Parsed order items if available


@dataclass  
class ProcessedTransaction:
    """Fully processed transaction with all enrichment."""
    transaction_id: str
    date: str
    description: str
    amount: float
    currency: str
    
    # Categorization
    category: str
    subcategory: str
    categorization_confidence: float
    categorization_method: str
    
    # Custom Category (if matched)
    custom_category_id: Optional[str]
    custom_category_name: Optional[str]
    custom_category_icon: Optional[str]
    
    # Split Info
    is_split: bool
    split_items: Optional[List[dict]]
    
    # Merchant Enrichment
    merchant_name: Optional[str]
    merchant_logo: Optional[str]
    merchant_business_type: Optional[str]
    charge_type: Optional[str]
    charge_description: Optional[str]
    supports_emi: bool
    is_subscription: bool

    # P2P Detection
    is_p2p: bool
    p2p_counterparty: Optional[str]
    p2p_direction: Optional[str]
    p2p_confidence: float

    # Tags
    tags: List[str]
    
    # Review flag
    needs_review: bool
    processed_at: str
    
    def to_dict(self):
        return asdict(self)


class SmartCategorizationPipeline:
    """
    Main pipeline class. Initialize once, call process() for each transaction.
    Thread-safe for batch processing.
    """
    
    def __init__(self,
                 feedback_path: str = os.path.join(_TMPDIR, "feedback_store.json"),
                 model_path: str = os.path.join(_TMPDIR, "cat_model.pkl"),
                 custom_cat_path: str = os.path.join(_TMPDIR, "custom_categories.json")):
        
        print("Initializing Smart Categorization Pipeline...")
        
        # Import all components
        from .categorizer import SmartCategorizationEngine
        from .split_handler import SplitTransactionHandler
        from .custom_categories import CustomCategoryBuilder
        from .enrichment import MerchantEnrichmentEngine
        from .p2p_detector import P2PDetector
        
        self.categorizer = SmartCategorizationEngine(feedback_path, model_path)
        self.splitter = SplitTransactionHandler()
        self.custom_cats = CustomCategoryBuilder(custom_cat_path)
        self.enricher = MerchantEnrichmentEngine()
        self.p2p = P2PDetector()
        
        print("Pipeline ready.")
    
    def process(self, transaction: Transaction) -> ProcessedTransaction:
        """
        Process a single transaction through the full pipeline.
        Returns a fully enriched ProcessedTransaction.
        """
        
        desc = transaction.description
        amt = abs(transaction.amount)  # Work with positive amounts
        
        # ── STEP 1: Base Categorization ─────────────────────────────────────
        cat_result = self.categorizer.categorize(
            description=desc,
            amount=amt,
            transaction_id=transaction.transaction_id
        )
        
        # ── STEP 1b: P2P Detection (runs BEFORE enrichment, can override) ───
        txn_type = "credit" if transaction.amount < 0 else "debit"
        p2p = self.p2p.detect(desc, amt, transaction_type=txn_type)
        if p2p.is_p2p:
            cat_result.predicted_category = "Transfers & Payments"
            cat_result.predicted_subcategory = p2p.suggested_subcategory
            cat_result.method = "p2p_detector"
            cat_result.confidence = p2p.confidence

        # ── STEP 2: Merchant Enrichment ──────────────────────────────────────
        enriched = self.enricher.enrich(
            description=desc,
            predicted_category=cat_result.predicted_category,
            predicted_subcategory=cat_result.predicted_subcategory,
            amount=amt
        )
        
        # ── STEP 3: Split Transaction Check ─────────────────────────────────
        split_result = None
        is_split = False
        split_items = None
        
        if self.splitter.should_split(desc, enriched.canonical_name):
            split_result = self.splitter.split(
                description=desc,
                amount=amt,
                line_items=transaction.line_items
            )
            if split_result.was_split:
                is_split = True
                split_items = [
                    {
                        "description": item.description,
                        "amount": item.amount,
                        "category": item.category,
                        "subcategory": item.subcategory,
                        "percentage": item.percentage
                    }
                    for item in split_result.split_items
                ]
        
        # ── STEP 4: Custom Category Check ────────────────────────────────────
        custom_cat = self.custom_cats.match_transaction(
            description=desc,
            amount=amt,
            date=transaction.date,
            merchant_name=enriched.canonical_name,
            original_category=cat_result.predicted_category
        )
        
        # ── STEP 5: Tag Compilation ──────────────────────────────────────────
        tags = list(cat_result.tags or [])
        if custom_cat:
            tags.extend(custom_cat.tags)
        if is_split:
            tags.append("split-transaction")
        if p2p.is_p2p:
            tags.append("p2p")
            tags.append(f"p2p-{p2p.direction}")
        if enriched.supports_emi:
            tags.append("emi-eligible")
        if enriched.charge_type == "subscription":
            tags.append("subscription")
        if transaction.amount < 0:
            tags.append("credit")
        tags = list(set(tags))  # Deduplicate
        
        # ── ASSEMBLE OUTPUT ──────────────────────────────────────────────────
        return ProcessedTransaction(
            transaction_id=transaction.transaction_id,
            date=transaction.date,
            description=desc,
            amount=transaction.amount,
            currency=transaction.currency,
            
            category=cat_result.predicted_category,
            subcategory=cat_result.predicted_subcategory,
            categorization_confidence=cat_result.confidence,
            categorization_method=cat_result.method,
            
            custom_category_id=custom_cat.category_id if custom_cat else None,
            custom_category_name=custom_cat.name if custom_cat else None,
            custom_category_icon=custom_cat.icon if custom_cat else None,
            
            is_split=is_split,
            split_items=split_items,
            
            merchant_name=enriched.canonical_name,
            merchant_logo=enriched.logo_url,
            merchant_business_type=enriched.business_type,
            charge_type=enriched.charge_type,
            charge_description=enriched.charge_description,
            supports_emi=enriched.supports_emi,
            is_subscription=(enriched.charge_type == "subscription"),

            is_p2p=p2p.is_p2p,
            p2p_counterparty=p2p.counterparty_name if p2p.is_p2p else None,
            p2p_direction=p2p.direction if p2p.is_p2p else None,
            p2p_confidence=p2p.confidence,

            tags=tags,
            needs_review=cat_result.needs_review,
            processed_at=datetime.now().isoformat()
        )
    
    def process_batch(self, transactions: List[Transaction],
                      verbose: bool = True) -> List[ProcessedTransaction]:
        """Process multiple transactions."""
        results = []
        total = len(transactions)
        
        for i, txn in enumerate(transactions):
            if verbose and i % 10 == 0:
                print(f"Processing {i+1}/{total}...")
            results.append(self.process(txn))
        
        if verbose:
            print(f"Processed {total} transactions")
        return results
    
    def correct_transaction(self, transaction_id: str, description: str,
                             merchant_name: Optional[str],
                             old_category: str, new_category: str,
                             new_subcategory: str):
        """
        User corrects a miscategorized transaction.
        System learns and applies to all future similar transactions.
        """
        self.categorizer.apply_correction(
            transaction_id=transaction_id,
            description=description,
            merchant_name=merchant_name,
            old_cat=old_category,
            new_cat=new_category,
            new_subcat=new_subcategory
        )
        print(f"Correction recorded: '{description[:40]}' -> {new_category} > {new_subcategory}")
        print("This will be applied to all future similar transactions automatically.")
    
    def create_custom_category(self, name: str, description: str,
                                keywords: List[str], merchants: List[str] = None,
                                budget_limit: float = None, color: str = "#6366F1",
                                icon: str = "folder"):
        """Quick method to create a custom category with keyword rules."""
        from .custom_categories import RuleType
        
        rules = [{"type": RuleType.KEYWORD, "value": kw} for kw in keywords]
        if merchants:
            rules += [{"type": RuleType.MERCHANT, "value": m} for m in merchants]
        
        cat = self.custom_cats.create_category(
            name=name,
            description=description,
            color=color,
            icon=icon,
            rules=rules,
            budget_limit=budget_limit
        )
        print(f"Custom category '{name}' created with {len(rules)} rules")
        return cat
    
    def get_summary(self, results: List[ProcessedTransaction]) -> dict:
        """Generate category summary from processed transactions."""
        from collections import defaultdict
        
        summary = defaultdict(lambda: {"total": 0, "count": 0, "transactions": []})
        subscriptions = []
        needs_review = []
        
        for r in results:
            key = f"{r.category} > {r.subcategory}"
            summary[key]["total"] += abs(r.amount)
            summary[key]["count"] += 1
            
            if r.is_subscription and r.amount > 0:
                subscriptions.append({
                    "merchant": r.merchant_name,
                    "amount": abs(r.amount),
                    "charge_type": r.charge_type
                })
            if r.needs_review:
                needs_review.append(r.transaction_id)
        
        return {
            "total_transactions": len(results),
            "total_spend": sum(abs(r.amount) for r in results if r.amount > 0),
            "categories": dict(summary),
            "subscriptions": subscriptions,
            "needs_review_count": len(needs_review),
            "needs_review_ids": needs_review,
            "split_transactions": sum(1 for r in results if r.is_split)
        }