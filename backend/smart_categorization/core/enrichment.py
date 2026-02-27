"""
Merchant Enrichment Engine
Adds logo, business type, charge type metadata to any transaction.
Handles unknown merchants via fuzzy matching + external enrichment.
"""

import re
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class EnrichedMerchant:
    canonical_name: str
    display_name: str
    logo_url: Optional[str]
    category: str
    subcategory: str
    business_type: str
    charge_type: str           # "subscription" | "one_time" | "variable" | "recurring_variable"
    charge_description: str   # Human-readable e.g. "Monthly subscription - ₹149 to ₹649"
    is_indian: bool
    is_online: bool
    supports_emi: bool
    website: Optional[str]
    contact: Optional[str]
    typical_range: Optional[str]
    confidence: float          # Enrichment confidence 0-1
    enrichment_source: str     # "merchant_db" | "fuzzy_match" | "pattern_inferred"


# ─────────────────────────────────────────────
# LOGO CDN URLS (use Clearbit-style URL patterns)
# In production: host on your own CDN or use Brandfetch API
# ─────────────────────────────────────────────

LOGO_CDN = {
    "zomato": "https://b.zmtcdn.com/web_assets/b40b97e677bc7b2ca77c58c61db266fe1603954218.png",
    "swiggy": "https://logos-world.net/wp-content/uploads/2022/07/Swiggy-Logo.png",
    "amazon": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
    "flipkart": "https://logos-world.net/wp-content/uploads/2020/11/Flipkart-Logo.png",
    "netflix": "https://upload.wikimedia.org/wikipedia/commons/7/7a/Logonetflix.png",
    "spotify": "https://upload.wikimedia.org/wikipedia/commons/2/26/Spotify_logo_with_text.svg",
    "uber": "https://upload.wikimedia.org/wikipedia/commons/c/cc/Uber_logo_2018.png",
    "ola": "https://logos-world.net/wp-content/uploads/2021/08/Ola-Logo.png",
    "paytm": "https://logos-world.net/wp-content/uploads/2020/09/Paytm-Logo.png",
    "phonepe": "https://download.logo.wine/logo/PhonePe/PhonePe-Logo.wine.png",
    "gpay": "https://upload.wikimedia.org/wikipedia/commons/f/f2/Google_Pay_Logo.svg",
    "jio": "https://logos-world.net/wp-content/uploads/2021/03/Jio-Logo.png",
    "airtel": "https://upload.wikimedia.org/wikipedia/commons/9/95/Bharti_Airtel_Logo.svg",
    "hdfc": "https://upload.wikimedia.org/wikipedia/commons/2/28/HDFC_Bank_Logo.svg",
    "sbi": "https://upload.wikimedia.org/wikipedia/commons/c/cc/SBI-logo.svg",
    "icici": "https://upload.wikimedia.org/wikipedia/commons/b/bb/Icici-bank-logo.svg",
}

# ─────────────────────────────────────────────
# BUSINESS TYPE DESCRIPTIONS
# ─────────────────────────────────────────────

BUSINESS_TYPE_INFO = {
    "food_delivery": {"display": "Food Delivery Platform", "typical_charge": "variable"},
    "quick_commerce": {"display": "Quick Commerce / 10-min Delivery", "typical_charge": "variable"},
    "ecommerce": {"display": "E-Commerce Marketplace", "typical_charge": "variable"},
    "ride_hailing": {"display": "Ride-Hailing / Cab Service", "typical_charge": "variable"},
    "ott": {"display": "OTT Streaming Platform", "typical_charge": "subscription"},
    "music_streaming": {"display": "Music Streaming Service", "typical_charge": "subscription"},
    "telecom": {"display": "Telecom / Mobile Operator", "typical_charge": "subscription"},
    "bank": {"display": "Bank / Financial Institution", "typical_charge": "variable"},
    "fintech": {"display": "Fintech / Digital Finance", "typical_charge": "variable"},
    "stockbroker": {"display": "Stock Broker / Investment Platform", "typical_charge": "variable"},
    "insurance": {"display": "Insurance Provider", "typical_charge": "subscription"},
    "pharmacy": {"display": "Pharmacy / Medical Store", "typical_charge": "variable"},
    "online_pharmacy": {"display": "Online Pharmacy", "typical_charge": "variable"},
    "healthtech": {"display": "Health-Tech Platform", "typical_charge": "variable"},
    "edtech": {"display": "Education Technology Platform", "typical_charge": "subscription"},
    "qsr": {"display": "Quick Service Restaurant (QSR)", "typical_charge": "variable"},
    "cafe": {"display": "Cafe / Coffee Shop", "typical_charge": "variable"},
    "supermarket": {"display": "Supermarket / Grocery Store", "typical_charge": "variable"},
    "electronics_retail": {"display": "Electronics Retail Store", "typical_charge": "variable"},
    "hospitality": {"display": "Hotels & Accommodation", "typical_charge": "variable"},
    "travel_ota": {"display": "Travel OTA (Online Travel Agency)", "typical_charge": "variable"},
    "airline": {"display": "Airline", "typical_charge": "one_time"},
    "fuel": {"display": "Petrol Pump / Fuel Station", "typical_charge": "variable"},
    "power_utility": {"display": "Electricity Distribution Company", "typical_charge": "variable"},
    "gas_utility": {"display": "City Gas Distribution", "typical_charge": "variable"},
    "government": {"display": "Government / Public Service", "typical_charge": "variable"},
    "tech": {"display": "Technology / Software Company", "typical_charge": "subscription"},
    "social_commerce": {"display": "Social Commerce Platform", "typical_charge": "variable"},
    "fashion_ecommerce": {"display": "Fashion E-Commerce", "typical_charge": "variable"},
    "beauty_ecommerce": {"display": "Beauty & Cosmetics Platform", "typical_charge": "variable"},
    "fitness": {"display": "Fitness & Wellness Platform", "typical_charge": "subscription"},
    "home_services": {"display": "Home Services Platform", "typical_charge": "variable"},
    "rail": {"display": "Indian Railways / Train Booking", "typical_charge": "variable"},
    "public_transit": {"display": "Public Transit / Metro", "typical_charge": "variable"},
    "grocery_ecommerce": {"display": "Online Grocery Platform", "typical_charge": "variable"},
}

CHARGE_TYPE_DESCRIPTIONS = {
    "subscription": "Recurring fixed subscription charge",
    "one_time": "One-time purchase",
    "variable": "Variable amount per transaction",
    "recurring_variable": "Recurring but amount varies (e.g., utility bills)",
}


class MerchantEnrichmentEngine:
    """
    Enriches raw transaction descriptions with merchant metadata.
    """
    
    def __init__(self):
        from ..data.merchant_db import find_merchant, MERCHANT_LOOKUP
        self.find_merchant = find_merchant
        self.merchant_lookup = MERCHANT_LOOKUP
    
    def enrich(self, description: str, predicted_category: str,
               predicted_subcategory: str, amount: float) -> EnrichedMerchant:
        """
        Main enrichment method. Returns full EnrichedMerchant object.
        """
        
        # Try exact / partial match
        merchant = self.find_merchant(description)
        
        if merchant:
            return self._enrich_from_record(merchant, 0.95, "merchant_db")
        
        # Try fuzzy match
        fuzzy = self._fuzzy_match(description)
        if fuzzy and fuzzy[1] > 0.75:
            return self._enrich_from_record(fuzzy[0], fuzzy[1] * 0.85, "fuzzy_match")
        
        # Infer from category
        return self._infer_from_category(
            description, predicted_category, predicted_subcategory, amount)
    
    def _enrich_from_record(self, merchant, confidence: float,
                             source: str) -> EnrichedMerchant:
        """Build EnrichedMerchant from a MerchantRecord."""
        biz_info = BUSINESS_TYPE_INFO.get(merchant.business_type, {})
        charge_desc = CHARGE_TYPE_DESCRIPTIONS.get(
            merchant.charge_type, "Variable charge")
        
        # Append typical range if available
        if merchant.typical_range:
            charge_desc += f" — typical range {merchant.typical_range}"
        
        logo = merchant.logo_url or self._get_logo(merchant.name)
        
        return EnrichedMerchant(
            canonical_name=merchant.name,
            display_name=merchant.name,
            logo_url=logo,
            category=merchant.category,
            subcategory=merchant.subcategory,
            business_type=biz_info.get("display", merchant.business_type),
            charge_type=merchant.charge_type,
            charge_description=charge_desc,
            is_indian=merchant.is_indian,
            is_online=merchant.is_online,
            supports_emi=merchant.supports_emi,
            website=None,  # Expand in production
            contact=None,
            typical_range=merchant.typical_range,
            confidence=confidence,
            enrichment_source=source
        )
    
    def _fuzzy_match(self, description: str):
        """Fuzzy match description against known merchant aliases."""
        desc_lower = description.lower()
        best_score = 0
        best_merchant = None
        
        # Extract first meaningful token (merchant names usually at start)
        words = desc_lower.split()[:4]
        short_desc = ' '.join(words)
        
        from ..data.merchant_db import MERCHANT_DB
        for record in MERCHANT_DB:
            for alias in record.aliases:
                score = SequenceMatcher(None, short_desc, alias.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_merchant = record
        
        if best_merchant and best_score > 0.6:
            return best_merchant, best_score
        return None
    
    def _infer_from_category(self, description: str, category: str,
                              subcategory: str, amount: float) -> EnrichedMerchant:
        """Infer enrichment from predicted category when merchant is unknown."""
        
        # Guess charge type from category
        sub_lower = subcategory.lower()
        if any(s in sub_lower for s in ["subscription", "ott", "streaming", "membership"]):
            charge_type = "subscription"
        elif any(s in sub_lower for s in ["bill", "electricity", "gas", "water"]):
            charge_type = "recurring_variable"
        elif any(s in sub_lower for s in ["loan", "emi", "insurance premium"]):
            charge_type = "subscription"
        else:
            charge_type = "variable"
        
        return EnrichedMerchant(
            canonical_name=self._extract_name(description),
            display_name=self._extract_name(description),
            logo_url=None,
            category=category,
            subcategory=subcategory,
            business_type=self._infer_biz_type(category, subcategory),
            charge_type=charge_type,
            charge_description=CHARGE_TYPE_DESCRIPTIONS[charge_type],
            is_indian=True,
            is_online=True,
            supports_emi=False,
            website=None,
            contact=None,
            typical_range=None,
            confidence=0.5,
            enrichment_source="pattern_inferred"
        )
    
    def _get_logo(self, merchant_name: str) -> Optional[str]:
        name_lower = merchant_name.lower()
        for key, url in LOGO_CDN.items():
            if key in name_lower:
                return url
        return None
    
    def _extract_name(self, description: str) -> str:
        """Extract likely merchant name from raw description."""
        # Remove common UPI suffixes
        cleaned = re.sub(
            r'(upi|payment|purchase|order|txn|ref|transfer|bill|pay).*',
            '', description, flags=re.I
        ).strip()
        # Title case first 3 words
        words = cleaned.split()[:3]
        return ' '.join(w.capitalize() for w in words) if words else description[:30]
    
    def _infer_biz_type(self, category: str, subcategory: str) -> str:
        mapping = {
            ("Food & Dining", "Restaurants"): "Food Delivery / Restaurant",
            ("Food & Dining", "Groceries"): "Grocery Store",
            ("Transportation", "Cab & Taxi"): "Ride-Hailing Service",
            ("Transportation", "Petrol & Fuel"): "Fuel Station",
            ("Entertainment", "OTT Subscriptions"): "OTT Streaming Platform",
            ("Utilities & Bills", "Mobile Recharge"): "Telecom Operator",
            ("Healthcare", "Pharmacy"): "Pharmacy / Medical Store",
            ("Financial Services", "Loan EMI"): "NBFC / Bank",
        }
        return mapping.get((category, subcategory), f"{category} Business")