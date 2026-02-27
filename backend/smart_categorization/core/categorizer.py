"""
Core Categorization Engine
- ML-based categorization using TF-IDF + Logistic Regression (no GPU needed)
- Contextual reclassification with user feedback learning
- Merchant dictionary lookup (primary) + ML fallback
"""

import re
import json
import pickle
import hashlib
import os
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

import tempfile
import numpy as np

# Cross-platform temp directory (works on Windows, Mac, Linux, Colab)
_TMPDIR = tempfile.gettempdir()

# ─────────────────────────────────────────────
# RESULT DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class CategorizationResult:
    transaction_id: str
    description: str
    amount: float
    predicted_category: str
    predicted_subcategory: str
    confidence: float                     # 0.0 - 1.0
    method: str                           # "merchant_db" | "ml_model" | "rule_based" | "user_override"
    merchant_record: Optional[dict] = None
    charge_type: Optional[str] = None     # subscription / one_time / variable
    business_type: Optional[str] = None
    logo_url: Optional[str] = None
    is_split: bool = False
    split_items: Optional[List[dict]] = None
    tags: List[str] = None
    needs_review: bool = False
    
    def to_dict(self):
        d = asdict(self)
        d['tags'] = self.tags or []
        return d

# ─────────────────────────────────────────────
# TRAINING DATA (seed patterns for ML model)
# ─────────────────────────────────────────────

TRAINING_DATA = [
    # (description, category, subcategory)
    ("zomato order food delivery", "Food & Dining", "Restaurants"),
    ("swiggy bundl technologies", "Food & Dining", "Restaurants"),
    ("blinkit quick commerce grocery", "Food & Dining", "Groceries"),
    ("zepto order groceries", "Food & Dining", "Groceries"),
    ("bigbasket order fresh vegetables", "Food & Dining", "Groceries"),
    ("dominos pizza order", "Food & Dining", "Fast Food"),
    ("mcdonalds burger restaurant", "Food & Dining", "Fast Food"),
    ("starbucks coffee purchase", "Food & Dining", "Cafes & Coffee"),
    ("uber cab ride bangalore", "Transportation", "Cab & Taxi"),
    ("ola cabs auto rickshaw", "Transportation", "Cab & Taxi"),
    ("rapido bike taxi commute", "Transportation", "Bike Rental"),
    ("irctc train ticket booking", "Transportation", "Metro & Train"),
    ("indigo airline ticket", "Travel & Accommodation", "Flight Tickets"),
    ("makemytrip flight hotel booking", "Travel & Accommodation", "Tour Packages"),
    ("oyo rooms hotel stay", "Travel & Accommodation", "Hotels & Resorts"),
    ("airtel prepaid recharge", "Utilities & Bills", "Mobile Recharge"),
    ("jio recharge plan", "Utilities & Bills", "Mobile Recharge"),
    ("netflix subscription monthly", "Entertainment", "OTT Subscriptions"),
    ("hotstar disney premium", "Entertainment", "OTT Subscriptions"),
    ("spotify premium music", "Entertainment", "OTT Subscriptions"),
    ("pvr cinemas movie ticket", "Entertainment", "Movies & Cinema"),
    ("bookmyshow event ticket concert", "Entertainment", "Movies & Cinema"),
    ("apollo pharmacy medicine", "Healthcare", "Pharmacy"),
    ("1mg online pharmacy order", "Healthcare", "Pharmacy"),
    ("practo doctor consultation", "Healthcare", "Doctor Consultation"),
    ("dr lal pathlabs blood test", "Healthcare", "Diagnostic Labs"),
    ("byjus subscription education", "Education", "Online Courses"),
    ("unacademy plus subscription", "Education", "Coaching & Tuitions"),
    ("zerodha brokerage trading", "Financial Services", "Stock Broking"),
    ("groww mutual fund sip", "Financial Services", "Mutual Funds"),
    ("lic premium insurance payment", "Financial Services", "Insurance Premium"),
    ("loan emi bajaj finserv payment", "Financial Services", "Loan EMI"),
    ("hdfc credit card bill payment", "Financial Services", "Credit Card Payment"),
    ("amazon india shopping electronics", "Shopping", "Electronics"),
    ("flipkart purchase mobile phone", "Shopping", "Electronics"),
    ("myntra fashion clothing purchase", "Shopping", "Clothing & Apparel"),
    ("meesho order clothing", "Shopping", "Clothing & Apparel"),
    ("nykaa beauty cosmetics order", "Personal Care", "Beauty & Cosmetics"),
    ("dmart supermarket grocery shop", "Shopping", "Grocery & Supermarket"),
    ("reliance fresh grocery purchase", "Shopping", "Grocery & Supermarket"),
    ("croma electronics purchase", "Shopping", "Electronics"),
    ("cult fit gym membership", "Personal Care", "Gym & Fitness"),
    ("urban company home services", "Home & Maintenance", "Housekeeping"),
    ("rent payment monthly home", "Home & Maintenance", "Rent"),
    ("electricity bill bescom payment", "Utilities & Bills", "Electricity"),
    ("gas bill igl png payment", "Utilities & Bills", "Gas (PNG/LPG)"),
    ("income tax payment tds", "Government & Taxes", "Income Tax"),
    ("gst payment gstn portal", "Government & Taxes", "GST Payment"),
    ("school fees tuition payment", "Education", "School Fees"),
    ("book purchase stationery store", "Shopping", "Books & Stationery"),
    ("petrol pump fuel refill", "Transportation", "Petrol & Fuel"),
    ("fastag toll highway", "Transportation", "Toll"),
    ("salary credit employer", "Transfers & Payments", "UPI Peer Transfer"),
    ("upi transfer send money", "Transfers & Payments", "UPI Peer Transfer"),
    ("paytm wallet topup", "Transfers & Payments", "Wallet Top-up"),
    ("donation charity ngo", "Charity & Donations", "NGO & Nonprofit"),
    ("temple donation religious", "Charity & Donations", "Religious Donations"),
    ("dream11 fantasy cricket", "Entertainment", "Gaming"),
    ("redbus bus ticket booking", "Transportation", "Inter-city Bus"),
    ("google one storage subscription", "Subscriptions & Memberships", "Cloud Storage"),
    ("microsoft office 365 subscription", "Subscriptions & Memberships", "Software & SaaS"),
]


# ─────────────────────────────────────────────
# ML CATEGORIZER
# ─────────────────────────────────────────────

class MLCategorizer:
    """
    TF-IDF + Logistic Regression for fallback categorization.
    Trains on seed data; re-trains when user feedback accumulates.
    """
    
    def __init__(self, model_path: str = os.path.join(_TMPDIR, "cat_model.pkl")):
        self.model_path = model_path
        self.vectorizer = None
        self.model = None
        self.label_encoder = None
        self._load_or_train()
    
    def _preprocess(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove common noise tokens
        noise = ['payment', 'purchase', 'txn', 'transaction', 'ref', 'upi', 'pg', 'gateway']
        tokens = [t for t in text.split() if t not in noise]
        return ' '.join(tokens)
    
    def _load_or_train(self):
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    saved = pickle.load(f)
                    self.vectorizer = saved['vectorizer']
                    self.model = saved['model']
                    self.label_encoder = saved['label_encoder']
                return
            except Exception:
                pass
        self.train(TRAINING_DATA)
    
    def train(self, data: list):
        """Train on list of (description, category, subcategory) tuples."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import LabelEncoder
        except ImportError:
            print("scikit-learn not installed. Run: pip install scikit-learn")
            return
        
        descriptions = [self._preprocess(d) for d, c, s in data]
        # Label: "Category > Subcategory"
        labels = [f"{c} > {s}" for d, c, s in data]
        
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)
        
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            min_df=1
        )
        X = self.vectorizer.fit_transform(descriptions)
        
        self.model = LogisticRegression(
            max_iter=500,
            C=2.0,
            solver='lbfgs',
            
        )
        self.model.fit(X, y)
        
        # Save (silent-fail: model stays in-memory if path is wrong/unwritable)
        try:
            save_dir = os.path.dirname(self.model_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'model': self.model,
                    'label_encoder': self.label_encoder
                }, f)
        except Exception as e:
            print(f"  WARN: Model save skipped ({e}). Running in-memory; continuing.")
    
    def predict(self, description: str) -> Tuple[str, str, float]:
        """Returns (category, subcategory, confidence)"""
        if self.model is None:
            return "Shopping", "Electronics", 0.1
        
        processed = self._preprocess(description)
        X = self.vectorizer.transform([processed])
        
        proba = self.model.predict_proba(X)[0]
        top_idx = np.argmax(proba)
        confidence = float(proba[top_idx])
        
        label = self.label_encoder.inverse_transform([top_idx])[0]
        parts = label.split(' > ')
        category = parts[0] if len(parts) > 0 else "Shopping"
        subcategory = parts[1] if len(parts) > 1 else "Electronics"
        
        return category, subcategory, confidence


# ─────────────────────────────────────────────
# USER FEEDBACK STORE  (Contextual Reclassification)
# ─────────────────────────────────────────────

class FeedbackStore:
    """
    Persists user corrections.
    Applies corrections to future similar transactions automatically.
    """
    
    def __init__(self, store_path: str = os.path.join(_TMPDIR, "feedback_store.json")):
        self.store_path = store_path
        self.corrections: Dict[str, dict] = {}  # pattern_hash → correction
        self.merchant_overrides: Dict[str, dict] = {}  # merchant_name → override
        self._load()
    
    def _load(self):
        if os.path.exists(self.store_path):
            with open(self.store_path) as f:
                data = json.load(f)
                self.corrections = data.get("corrections", {})
                self.merchant_overrides = data.get("merchant_overrides", {})
    
    def _save(self):
        try:
            save_dir = os.path.dirname(self.store_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
            with open(self.store_path, 'w') as f:
                json.dump({
                    "corrections": self.corrections,
                    "merchant_overrides": self.merchant_overrides
                }, f, indent=2)
        except Exception as e:
            print(f"  WARN: Feedback save skipped ({e}). Corrections active in-memory only.")
    
    def _description_hash(self, description: str) -> str:
        """Normalize description to a pattern key."""
        cleaned = re.sub(r'\d+', '', description.lower())
        cleaned = re.sub(r'[^a-z\s]', '', cleaned).strip()
        tokens = sorted(set(cleaned.split()))[:5]  # top 5 unique tokens
        return hashlib.md5(' '.join(tokens).encode()).hexdigest()
    
    def record_correction(self, description: str, merchant_name: Optional[str],
                          old_category: str, new_category: str, new_subcategory: str):
        """User corrects a transaction → store for future use."""
        pattern_hash = self._description_hash(description)
        correction = {
            "description_sample": description[:100],
            "category": new_category,
            "subcategory": new_subcategory,
            "corrected_at": datetime.now().isoformat(),
            "count": self.corrections.get(pattern_hash, {}).get("count", 0) + 1
        }
        self.corrections[pattern_hash] = correction
        
        # Also store merchant-level override
        if merchant_name:
            self.merchant_overrides[merchant_name.lower()] = {
                "category": new_category,
                "subcategory": new_subcategory
            }
        
        self._save()
    
    def check_override(self, description: str, merchant_name: Optional[str] = None
                       ) -> Optional[Tuple[str, str]]:
        """
        Check if there's a user override for this transaction.
        Returns (category, subcategory) or None.
        """
        # Merchant-level override (highest priority)
        if merchant_name and merchant_name.lower() in self.merchant_overrides:
            o = self.merchant_overrides[merchant_name.lower()]
            return o["category"], o["subcategory"]
        
        # Pattern-level override
        pattern_hash = self._description_hash(description)
        if pattern_hash in self.corrections:
            c = self.corrections[pattern_hash]
            return c["category"], c["subcategory"]
        
        return None
    
    def retrain_needed(self, threshold: int = 20) -> bool:
        """Returns True if enough corrections accumulated to warrant retraining."""
        return len(self.corrections) >= threshold


# ─────────────────────────────────────────────
# MAIN CATEGORIZATION ENGINE
# ─────────────────────────────────────────────

class SmartCategorizationEngine:
    """
    Orchestrates all categorization components.
    Priority: User Override → Merchant DB → ML Model → Rule Fallback
    """
    
    def __init__(self, feedback_path: str = os.path.join(_TMPDIR, "feedback_store.json"),
                 model_path: str = os.path.join(_TMPDIR, "cat_model.pkl")):
        from ..data.merchant_db import find_merchant
        self.find_merchant = find_merchant
        
        self.feedback = FeedbackStore(feedback_path)
        self.ml = MLCategorizer(model_path)
    
    def categorize(self, description: str, amount: float,
                   transaction_id: Optional[str] = None) -> CategorizationResult:
        
        txn_id = transaction_id or hashlib.md5(
            f"{description}{amount}".encode()).hexdigest()[:8]
        
        # 1. Find merchant from DB
        merchant = self.find_merchant(description)
        merchant_name = merchant.name if merchant else None
        
        # 2. Check user override (highest priority)
        override = self.feedback.check_override(description, merchant_name)
        if override:
            cat, subcat = override
            return CategorizationResult(
                transaction_id=txn_id,
                description=description,
                amount=amount,
                predicted_category=cat,
                predicted_subcategory=subcat,
                confidence=1.0,
                method="user_override",
                merchant_record=merchant.__dict__ if merchant else None,
                charge_type=merchant.charge_type if merchant else None,
                business_type=merchant.business_type if merchant else None,
                logo_url=merchant.logo_url if merchant else None,
                tags=self._generate_tags(cat, subcat, merchant, amount)
            )
        
        # 3. Merchant DB lookup
        if merchant:
            return CategorizationResult(
                transaction_id=txn_id,
                description=description,
                amount=amount,
                predicted_category=merchant.category,
                predicted_subcategory=merchant.subcategory,
                confidence=0.95,
                method="merchant_db",
                merchant_record=merchant.__dict__,
                charge_type=merchant.charge_type,
                business_type=merchant.business_type,
                logo_url=merchant.logo_url,
                tags=self._generate_tags(merchant.category, merchant.subcategory, merchant, amount),
                needs_review=False
            )
        
        # 4. ML model fallback
        cat, subcat, confidence = self.ml.predict(description)
        return CategorizationResult(
            transaction_id=txn_id,
            description=description,
            amount=amount,
            predicted_category=cat,
            predicted_subcategory=subcat,
            confidence=confidence,
            method="ml_model",
            needs_review=confidence < 0.60,
            tags=self._generate_tags(cat, subcat, None, amount)
        )
    
    def apply_correction(self, transaction_id: str, description: str,
                         merchant_name: Optional[str],
                         old_cat: str, new_cat: str, new_subcat: str):
        """User corrects a transaction category."""
        self.feedback.record_correction(
            description, merchant_name, old_cat, new_cat, new_subcat
        )
        # Optionally retrain if threshold reached
        if self.feedback.retrain_needed():
            self._incremental_retrain()
    
    def _incremental_retrain(self):
        """Add user corrections to training set and retrain model."""
        extra_data = []
        for _, correction in self.feedback.corrections.items():
            extra_data.append((
                correction["description_sample"],
                correction["category"],
                correction["subcategory"]
            ))
        combined = TRAINING_DATA + extra_data
        self.ml.train(combined)
    
    def _generate_tags(self, category: str, subcategory: str,
                       merchant, amount: float) -> List[str]:
        tags = []
        if merchant:
            if merchant.charge_type == "subscription":
                tags.append("subscription")
            if merchant.supports_emi:
                tags.append("emi-eligible")
            if not merchant.is_online:
                tags.append("offline-purchase")
        if amount > 10000:
            tags.append("large-expense")
        if "OTT" in subcategory or "subscription" in subcategory.lower():
            tags.append("recurring")
        return tags