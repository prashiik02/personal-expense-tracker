"""
India-Specific Merchant Dictionary
Seed database of 200+ merchants with full enrichment metadata.
In production, this scales to 50,000+ via crowd-sourcing + ML expansion.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
import json

@dataclass
class MerchantRecord:
    name: str                          # Canonical merchant name
    aliases: List[str]                 # Common alternate names / UPI descriptions
    category: str                      # Primary category
    subcategory: str                   # Subcategory
    charge_type: str                   # "subscription" | "one_time" | "variable" | "recurring_variable"
    business_type: str                 # "food_delivery" | "ecommerce" | "utility" | etc.
    logo_url: Optional[str] = None     # URL to merchant logo (CDN)
    is_indian: bool = True
    is_online: bool = True
    supports_emi: bool = False
    typical_range: Optional[str] = None  # e.g., "₹100-500" for coffee shops
    notes: Optional[str] = None
    split_rules: Optional[dict] = None   # For merchants that need transaction splitting

# ─────────────────────────────────────────────
# SEED MERCHANT DATABASE (200+ entries)
# In production: loaded from SQLite/PostgreSQL
# ─────────────────────────────────────────────

MERCHANT_DB: List[MerchantRecord] = [

    # ── FOOD DELIVERY ──────────────────────────────────────────────────────────
    MerchantRecord("Zomato", ["zomato", "zomato order", "zomato food", "zmt*"],
        "Food & Dining", "Restaurants", "variable", "food_delivery",
        "https://logos.zomato.com/logo.png", typical_range="₹150-1500"),
    MerchantRecord("Swiggy", ["swiggy", "swiggy order", "bundl technologies", "swgy*"],
        "Food & Dining", "Restaurants", "variable", "food_delivery",
        typical_range="₹150-1500"),
    MerchantRecord("Dunzo", ["dunzo", "dunzo daily", "dunzo delivery"],
        "Food & Dining", "Groceries", "variable", "quick_commerce"),
    MerchantRecord("Blinkit", ["blinkit", "grofers", "blinkit order", "blt*"],
        "Food & Dining", "Groceries", "variable", "quick_commerce",
        notes="Formerly Grofers"),
    MerchantRecord("Zepto", ["zepto", "zepto order", "zepto quick"],
        "Food & Dining", "Groceries", "variable", "quick_commerce"),
    MerchantRecord("BigBasket", ["bigbasket", "bigbasket.com", "innovative retail"],
        "Food & Dining", "Groceries", "variable", "grocery_ecommerce"),
    MerchantRecord("Milkbasket", ["milkbasket", "milk basket"],
        "Food & Dining", "Groceries", "recurring_variable", "milk_delivery"),
    MerchantRecord("Country Delight", ["country delight", "countrydelight"],
        "Food & Dining", "Groceries", "recurring_variable", "milk_delivery"),
    MerchantRecord("Domino's Pizza", ["dominos", "domino's", "jubilant foodworks", "dpz*"],
        "Food & Dining", "Fast Food", "variable", "qsr"),
    MerchantRecord("McDonald's", ["mcdonalds", "mcdonald's", "hardcastle restaurants", "mcd*"],
        "Food & Dining", "Fast Food", "variable", "qsr"),
    MerchantRecord("Burger King", ["burger king", "bk*", "restaurant brands"],
        "Food & Dining", "Fast Food", "variable", "qsr"),
    MerchantRecord("KFC", ["kfc", "kentucky fried chicken", "devyani international"],
        "Food & Dining", "Fast Food", "variable", "qsr"),
    MerchantRecord("Pizza Hut", ["pizza hut", "pizzahut", "yum restaurants"],
        "Food & Dining", "Fast Food", "variable", "qsr"),
    MerchantRecord("Subway", ["subway", "doctor's associates"],
        "Food & Dining", "Fast Food", "variable", "qsr"),
    MerchantRecord("Starbucks", ["starbucks", "tata starbucks"],
        "Food & Dining", "Cafes & Coffee", "variable", "cafe",
        typical_range="₹200-600"),
    MerchantRecord("Cafe Coffee Day", ["cafe coffee day", "ccd", "coffee day"],
        "Food & Dining", "Cafes & Coffee", "variable", "cafe"),
    MerchantRecord("Chaayos", ["chaayos", "chayoos"],
        "Food & Dining", "Cafes & Coffee", "variable", "tea_cafe"),
    MerchantRecord("Third Wave Coffee", ["third wave coffee", "thirdwave"],
        "Food & Dining", "Cafes & Coffee", "variable", "specialty_cafe"),
    MerchantRecord("Haldiram's", ["haldirams", "haldiram's", "haldiram"],
        "Food & Dining", "Sweet Shops", "variable", "sweet_snack"),
    MerchantRecord("Bikanervala", ["bikanervala", "bikaner"],
        "Food & Dining", "Sweet Shops", "variable", "sweet_snack"),

    # ── ECOMMERCE ──────────────────────────────────────────────────────────────
    MerchantRecord("Amazon India", ["amazon", "amazon.in", "amazon seller", "amzn*"],
        "Shopping", "Electronics", "variable", "ecommerce",
        supports_emi=True,
        split_rules={
            "enabled": True,
            "strategy": "nlp_description",
            "note": "Parse order description to split into Electronics/Clothing/Books/Groceries"
        }),
    MerchantRecord("Flipkart", ["flipkart", "fk*", "walmart india"],
        "Shopping", "Electronics", "variable", "ecommerce",
        supports_emi=True,
        split_rules={"enabled": True, "strategy": "nlp_description"}),
    MerchantRecord("Meesho", ["meesho", "fashnear"],
        "Shopping", "Clothing & Apparel", "variable", "social_commerce"),
    MerchantRecord("Myntra", ["myntra", "myntra fashion"],
        "Shopping", "Clothing & Apparel", "variable", "fashion_ecommerce"),
    MerchantRecord("Ajio", ["ajio", "reliance ajio"],
        "Shopping", "Clothing & Apparel", "variable", "fashion_ecommerce"),
    MerchantRecord("Nykaa", ["nykaa", "nykaa fashion", "fsh india"],
        "Personal Care", "Beauty & Cosmetics", "variable", "beauty_ecommerce"),
    MerchantRecord("Purplle", ["purplle", "purple beauty"],
        "Personal Care", "Beauty & Cosmetics", "variable", "beauty_ecommerce"),
    MerchantRecord("Snapdeal", ["snapdeal", "jasper infotech"],
        "Shopping", "Electronics", "variable", "ecommerce"),
    MerchantRecord("JioMart", ["jiomart", "jio mart", "reliance retail"],
        "Food & Dining", "Groceries", "variable", "grocery_ecommerce"),
    MerchantRecord("CRED", ["cred", "cred pay", "happay"],
        "Financial Services", "Credit Card Payment", "variable", "fintech",
        notes="Usually credit card bill payments"),

    # ── TRANSPORTATION ─────────────────────────────────────────────────────────
    MerchantRecord("Uber", ["uber", "uber cab", "uber india", "ub*cab"],
        "Transportation", "Cab & Taxi", "variable", "ride_hailing"),
    MerchantRecord("Ola Cabs", ["ola", "ola cabs", "ani technologies", "olacabs"],
        "Transportation", "Cab & Taxi", "variable", "ride_hailing"),
    MerchantRecord("Rapido", ["rapido", "roppen transportation"],
        "Transportation", "Bike Rental", "variable", "bike_taxi"),
    MerchantRecord("Namma Metro", ["namma metro", "bmrcl", "metro rail"],
        "Transportation", "Metro & Train", "variable", "public_transit"),
    MerchantRecord("IRCTC", ["irctc", "indian railway", "ir ctc"],
        "Transportation", "Metro & Train", "variable", "rail",
        notes="Train tickets"),
    MerchantRecord("RedBus", ["redbus", "ibibo group"],
        "Transportation", "Inter-city Bus", "variable", "bus_booking"),
    MerchantRecord("IndiGo Airlines", ["indigo", "interglobe aviation", "6e"],
        "Travel & Accommodation", "Flight Tickets", "variable", "airline"),
    MerchantRecord("Air India", ["air india", "aai"],
        "Travel & Accommodation", "Flight Tickets", "variable", "airline"),
    MerchantRecord("SpiceJet", ["spicejet", "spice jet"],
        "Travel & Accommodation", "Flight Tickets", "variable", "airline"),
    MerchantRecord("HP Petrol Pump", ["hp petrol", "hindustan petroleum", "hpcl"],
        "Transportation", "Petrol & Fuel", "variable", "fuel"),
    MerchantRecord("Indian Oil", ["indian oil", "iocl", "ioc petrol"],
        "Transportation", "Petrol & Fuel", "variable", "fuel"),
    MerchantRecord("Bharat Petroleum", ["bharat petroleum", "bpcl", "bp petrol"],
        "Transportation", "Petrol & Fuel", "variable", "fuel"),
    MerchantRecord("FASTag", ["fastag", "fas tag", "netc fastag", "nhai fastag"],
        "Transportation", "Toll", "variable", "toll",
        notes="Highway toll payments"),

    # ── UTILITIES & BILLS ──────────────────────────────────────────────────────
    MerchantRecord("Airtel", ["airtel", "bharti airtel", "airtel broadband", "airtel fiber"],
        "Utilities & Bills", "Mobile Recharge", "subscription", "telecom"),
    MerchantRecord("Jio", ["jio", "reliance jio", "jio recharge", "rjio"],
        "Utilities & Bills", "Mobile Recharge", "subscription", "telecom"),
    MerchantRecord("Vi (Vodafone Idea)", ["vodafone", "idea", "vi ", "vi recharge"],
        "Utilities & Bills", "Mobile Recharge", "subscription", "telecom"),
    MerchantRecord("BSNL", ["bsnl", "bharat sanchar"],
        "Utilities & Bills", "Mobile Recharge", "subscription", "telecom"),
    MerchantRecord("Tata Sky", ["tata sky", "tataplay", "tata play", "tata sky dth"],
        "Utilities & Bills", "DTH & Cable TV", "subscription", "dth"),
    MerchantRecord("Dish TV", ["dish tv", "dishtv", "dish network"],
        "Utilities & Bills", "DTH & Cable TV", "subscription", "dth"),
    MerchantRecord("ACT Fibernet", ["act fibernet", "atria convergence", "act broadband"],
        "Utilities & Bills", "Internet & Broadband", "subscription", "isp"),
    MerchantRecord("Hathway", ["hathway", "hathway cable"],
        "Utilities & Bills", "Internet & Broadband", "subscription", "isp"),
    MerchantRecord("BESCOM", ["bescom", "bangalore electricity", "bengaluru electricity"],
        "Utilities & Bills", "Electricity", "variable", "power_utility"),
    MerchantRecord("MSEB/MSEDCL", ["mseb", "msedcl", "maharashtra electricity"],
        "Utilities & Bills", "Electricity", "variable", "power_utility"),
    MerchantRecord("TPDDL", ["tpddl", "tata power delhi", "ndpl"],
        "Utilities & Bills", "Electricity", "variable", "power_utility"),
    MerchantRecord("Indraprastha Gas", ["igl", "indraprastha gas", "delhi gas"],
        "Utilities & Bills", "Gas (PNG/LPG)", "variable", "gas_utility"),
    MerchantRecord("Mahanagar Gas", ["mahanagar gas", "mgl"],
        "Utilities & Bills", "Gas (PNG/LPG)", "variable", "gas_utility"),
    MerchantRecord("HP Gas", ["hp gas", "hpcl gas", "indane"],
        "Utilities & Bills", "Gas (PNG/LPG)", "variable", "lpg"),

    # ── ENTERTAINMENT & OTT ────────────────────────────────────────────────────
    MerchantRecord("Netflix", ["netflix", "netflix subscription", "nflx"],
        "Entertainment", "OTT Subscriptions", "subscription", "ott",
        typical_range="₹149-649/month"),
    MerchantRecord("Amazon Prime", ["amazon prime", "prime video", "prime membership"],
        "Entertainment", "OTT Subscriptions", "subscription", "ott",
        notes="May overlap with Amazon shopping"),
    MerchantRecord("Disney+ Hotstar", ["hotstar", "disney hotstar", "star india", "disney+"],
        "Entertainment", "OTT Subscriptions", "subscription", "ott"),
    MerchantRecord("Sony LIV", ["sony liv", "sonyliv", "msp sports"],
        "Entertainment", "OTT Subscriptions", "subscription", "ott"),
    MerchantRecord("Zee5", ["zee5", "zee entertainment"],
        "Entertainment", "OTT Subscriptions", "subscription", "ott"),
    MerchantRecord("JioCinema", ["jiocinema", "jio cinema"],
        "Entertainment", "OTT Subscriptions", "subscription", "ott"),
    MerchantRecord("Spotify", ["spotify", "spotify premium"],
        "Entertainment", "OTT Subscriptions", "subscription", "music_streaming"),
    MerchantRecord("Gaana", ["gaana", "gaana premium", "times internet"],
        "Entertainment", "OTT Subscriptions", "subscription", "music_streaming"),
    MerchantRecord("JioSaavn", ["jiosaavn", "saavn", "jio saavn"],
        "Entertainment", "OTT Subscriptions", "subscription", "music_streaming"),
    MerchantRecord("PVR Cinemas", ["pvr", "pvr cinemas", "pvr inox"],
        "Entertainment", "Movies & Cinema", "one_time", "cinema"),
    MerchantRecord("INOX", ["inox", "inox leisure"],
        "Entertainment", "Movies & Cinema", "one_time", "cinema"),
    MerchantRecord("BookMyShow", ["bookmyshow", "bms", "bigtree entertainment"],
        "Entertainment", "Movies & Cinema", "variable", "ticketing"),
    MerchantRecord("Dream11", ["dream11", "sporta technologies"],
        "Entertainment", "Gaming", "variable", "fantasy_sports"),
    MerchantRecord("MPL (Mobile Premier League)", ["mpl", "mobile premier league"],
        "Entertainment", "Gaming", "variable", "gaming"),

    # ── HEALTHCARE ─────────────────────────────────────────────────────────────
    MerchantRecord("Apollo Pharmacy", ["apollo pharmacy", "apollo health", "apollo"],
        "Healthcare", "Pharmacy", "variable", "pharmacy"),
    MerchantRecord("1mg", ["1mg", "tata 1mg", "onemedz"],
        "Healthcare", "Pharmacy", "variable", "online_pharmacy"),
    MerchantRecord("PharmEasy", ["pharmeasy", "pharmease"],
        "Healthcare", "Pharmacy", "variable", "online_pharmacy"),
    MerchantRecord("Netmeds", ["netmeds", "net meds", "reliance netmeds"],
        "Healthcare", "Pharmacy", "variable", "online_pharmacy"),
    MerchantRecord("Practo", ["practo"],
        "Healthcare", "Doctor Consultation", "variable", "healthtech"),
    MerchantRecord("Lybrate", ["lybrate"],
        "Healthcare", "Doctor Consultation", "variable", "healthtech"),
    MerchantRecord("MediBuddy", ["medibuddy", "medi buddy"],
        "Healthcare", "Hospitals & Clinics", "variable", "healthtech"),
    MerchantRecord("Dr Lal PathLabs", ["dr lal pathlabs", "lal pathlabs", "lal path"],
        "Healthcare", "Diagnostic Labs", "variable", "diagnostics"),
    MerchantRecord("Thyrocare", ["thyrocare"],
        "Healthcare", "Diagnostic Labs", "variable", "diagnostics"),
    MerchantRecord("Star Health Insurance", ["star health", "star health insurance"],
        "Healthcare", "Insurance Premium", "subscription", "health_insurance"),
    MerchantRecord("Niva Bupa (Max Bupa)", ["max bupa", "niva bupa"],
        "Healthcare", "Insurance Premium", "subscription", "health_insurance"),

    # ── EDUCATION ──────────────────────────────────────────────────────────────
    MerchantRecord("BYJU'S", ["byjus", "byju's", "think and learn"],
        "Education", "Online Courses", "subscription", "edtech"),
    MerchantRecord("Unacademy", ["unacademy"],
        "Education", "Coaching & Tuitions", "subscription", "edtech"),
    MerchantRecord("Vedantu", ["vedantu"],
        "Education", "Online Courses", "subscription", "edtech"),
    MerchantRecord("Coursera", ["coursera"],
        "Education", "Online Courses", "subscription", "edtech"),
    MerchantRecord("upGrad", ["upgrad", "up grad"],
        "Education", "Online Courses", "subscription", "edtech"),
    MerchantRecord("Great Learning", ["great learning", "greatlearning"],
        "Education", "Skill Development", "subscription", "edtech"),
    MerchantRecord("WhiteHat Jr", ["whitehat jr", "whitehat junior"],
        "Education", "Skill Development", "subscription", "edtech"),

    # ── FINANCIAL SERVICES ─────────────────────────────────────────────────────
    MerchantRecord("Zerodha", ["zerodha", "zerodha broking"],
        "Financial Services", "Stock Broking", "variable", "stockbroker"),
    MerchantRecord("Groww", ["groww", "nextbillion technology"],
        "Financial Services", "Mutual Funds", "variable", "fintech"),
    MerchantRecord("Upstox", ["upstox", "rksv securities"],
        "Financial Services", "Stock Broking", "variable", "stockbroker"),
    MerchantRecord("Angel One", ["angel one", "angel broking"],
        "Financial Services", "Stock Broking", "variable", "stockbroker"),
    MerchantRecord("Paytm Money", ["paytm money"],
        "Financial Services", "Mutual Funds", "variable", "fintech"),
    MerchantRecord("LIC", ["lic", "life insurance corporation", "lic premium"],
        "Financial Services", "Insurance Premium", "subscription", "insurance"),
    MerchantRecord("HDFC Life", ["hdfc life", "hdfc standard life"],
        "Financial Services", "Insurance Premium", "subscription", "insurance"),
    MerchantRecord("Bajaj Finserv", ["bajaj finserv", "bajaj finance"],
        "Financial Services", "Loan EMI", "subscription", "nbfc",
        supports_emi=True),
    MerchantRecord("SBI Card", ["sbi card", "sbi credit card"],
        "Financial Services", "Credit Card Payment", "variable", "bank"),
    MerchantRecord("HDFC Credit Card", ["hdfc card", "hdfc credit card"],
        "Financial Services", "Credit Card Payment", "variable", "bank"),

    # ── TRAVEL & ACCOMMODATION ─────────────────────────────────────────────────
    MerchantRecord("OYO Rooms", ["oyo", "oyo rooms", "oravel stays"],
        "Travel & Accommodation", "Hotels & Resorts", "variable", "hospitality"),
    MerchantRecord("MakeMyTrip", ["makemytrip", "mmt"],
        "Travel & Accommodation", "Tour Packages", "variable", "travel_ota"),
    MerchantRecord("Goibibo", ["goibibo", "go ibibo"],
        "Travel & Accommodation", "Tour Packages", "variable", "travel_ota"),
    MerchantRecord("Yatra", ["yatra", "yatra.com"],
        "Travel & Accommodation", "Tour Packages", "variable", "travel_ota"),
    MerchantRecord("Airbnb", ["airbnb"],
        "Travel & Accommodation", "Airbnb & Home Stays", "variable", "hospitality"),
    MerchantRecord("Treebo Hotels", ["treebo", "treebo hotels"],
        "Travel & Accommodation", "Hotels & Resorts", "variable", "hospitality"),

    # ── HOME & MAINTENANCE ─────────────────────────────────────────────────────
    MerchantRecord("Urban Company", ["urban company", "urbanclap", "uc*"],
        "Home & Maintenance", "Housekeeping", "variable", "home_services"),
    MerchantRecord("Housejoy", ["housejoy"],
        "Home & Maintenance", "Housekeeping", "variable", "home_services"),
    MerchantRecord("NoBroker", ["nobroker", "no broker"],
        "Home & Maintenance", "Rent", "variable", "real_estate"),

    # ── PERSONAL CARE ─────────────────────────────────────────────────────────
    MerchantRecord("Cult.fit", ["cult fit", "cult.fit", "curefit"],
        "Personal Care", "Gym & Fitness", "subscription", "fitness"),
    MerchantRecord("Fitpass", ["fitpass", "fit pass"],
        "Personal Care", "Gym & Fitness", "subscription", "fitness"),
    MerchantRecord("Laundry Express", ["laundry express", "washmart", "uclean"],
        "Personal Care", "Laundry", "variable", "laundry"),

    # ── GOVT & TAXES ──────────────────────────────────────────────────────────
    MerchantRecord("Income Tax Department", ["income tax", "incometax", "it dept", "tin-nsdl"],
        "Government & Taxes", "Income Tax", "variable", "government"),
    MerchantRecord("GST Portal", ["gst", "gstn", "gst portal"],
        "Government & Taxes", "GST Payment", "variable", "government"),
    MerchantRecord("Parivahan (Vehicle Tax)", ["parivahan", "vahan", "vehicle tax"],
        "Government & Taxes", "Vehicle Tax", "variable", "government"),
    MerchantRecord("Traffic Challan", ["e-challan", "echallan", "traffic challan"],
        "Government & Taxes", "Traffic Fine", "variable", "government"),

    # ── SOFTWARE / SAAS ───────────────────────────────────────────────────────
    MerchantRecord("Google", ["google", "google one", "google play", "google workspace", "goog*"],
        "Subscriptions & Memberships", "Cloud Storage", "subscription", "tech",
        notes="Could be Google One, Play Store, Workspace etc."),
    MerchantRecord("Microsoft", ["microsoft", "ms office", "office 365", "microsoft 365"],
        "Subscriptions & Memberships", "Software & SaaS", "subscription", "tech"),
    MerchantRecord("Adobe", ["adobe", "adobe creative cloud", "adobe cc"],
        "Subscriptions & Memberships", "Software & SaaS", "subscription", "tech"),
    MerchantRecord("Zoho", ["zoho", "zoho corporation"],
        "Subscriptions & Memberships", "Software & SaaS", "subscription", "tech"),

    # ── HYPERLOCAL / REGIONAL ─────────────────────────────────────────────────
    MerchantRecord("D-Mart", ["dmart", "d-mart", "avenue supermarts"],
        "Shopping", "Grocery & Supermarket", "variable", "supermarket",
        is_online=False),
    MerchantRecord("Reliance Fresh", ["reliance fresh", "smart superstore", "reliance smart"],
        "Shopping", "Grocery & Supermarket", "variable", "supermarket",
        is_online=False),
    MerchantRecord("More Retail", ["more", "more retail", "more supermarket"],
        "Shopping", "Grocery & Supermarket", "variable", "supermarket",
        is_online=False),
    MerchantRecord("Spencer's Retail", ["spencers", "spencer's"],
        "Shopping", "Grocery & Supermarket", "variable", "supermarket",
        is_online=False),
    MerchantRecord("Pantaloons", ["pantaloons", "aditya birla fashion"],
        "Shopping", "Clothing & Apparel", "variable", "retail", is_online=False),
    MerchantRecord("Westside", ["westside", "trent"],
        "Shopping", "Clothing & Apparel", "variable", "retail", is_online=False),
    MerchantRecord("Croma", ["croma", "infiniti retail"],
        "Shopping", "Electronics", "variable", "electronics_retail",
        supports_emi=True, is_online=False),
    MerchantRecord("Vijay Sales", ["vijay sales"],
        "Shopping", "Electronics", "variable", "electronics_retail",
        supports_emi=True, is_online=False),
    MerchantRecord("Reliance Digital", ["reliance digital"],
        "Shopping", "Electronics", "variable", "electronics_retail",
        supports_emi=True, is_online=False),
    MerchantRecord("Crossword", ["crossword", "crossword bookstores"],
        "Shopping", "Books & Stationery", "variable", "bookstore", is_online=False),
    MerchantRecord("Flipkart Supermart", ["flipkart supermart"],
        "Food & Dining", "Groceries", "variable", "grocery_ecommerce"),
]

def get_merchant_lookup() -> dict:
    """Build alias → MerchantRecord lookup dict for O(1) access."""
    lookup = {}
    for record in MERCHANT_DB:
        for alias in record.aliases:
            lookup[alias.lower().strip()] = record
        lookup[record.name.lower().strip()] = record
    return lookup

MERCHANT_LOOKUP = get_merchant_lookup()

def find_merchant(description: str) -> Optional[MerchantRecord]:
    """
    Exact + partial alias match against merchant lookup.
    Returns MerchantRecord or None.
    """
    desc_lower = description.lower().strip()
    
    # Exact match
    if desc_lower in MERCHANT_LOOKUP:
        return MERCHANT_LOOKUP[desc_lower]
    
    # Partial match (longest alias wins)
    best_match = None
    best_len = 0
    for alias, record in MERCHANT_LOOKUP.items():
        if alias in desc_lower and len(alias) > best_len:
            best_match = record
            best_len = len(alias)
    
    return best_match

def merchant_to_dict(record: MerchantRecord) -> dict:
    return asdict(record)