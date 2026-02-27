"""
India-Specific Category Taxonomy
Full hierarchy of categories and subcategories used throughout the system.
"""

CATEGORY_TAXONOMY = {
    "Food & Dining": {
        "subcategories": [
            "Restaurants", "Fast Food", "Cafes & Coffee", "Street Food",
            "Groceries", "Bakeries", "Sweet Shops", "Juice Bars",
            "Cloud Kitchens", "Tiffin Services", "Alcohol & Beverages"
        ],
        "keywords": ["food", "restaurant", "cafe", "kitchen", "sweets", "dhaba", "biryani",
                     "pizza", "burger", "chai", "coffee", "juice", "bakery"]
    },
    "Shopping": {
        "subcategories": [
            "Electronics", "Clothing & Apparel", "Books & Stationery",
            "Home & Furniture", "Footwear", "Jewellery", "Gifts & Toys",
            "Grocery & Supermarket", "Pharmacy & Health Products",
            "Hardware & Tools", "Sports & Fitness Equipment"
        ],
        "keywords": ["store", "shop", "mart", "bazaar", "emporium", "outlet",
                     "mall", "market", "wholesale"]
    },
    "Transportation": {
        "subcategories": [
            "Cab & Taxi", "Auto Rickshaw", "Metro & Train", "Bus",
            "Petrol & Fuel", "Parking", "Toll", "Flight", "EV Charging",
            "Bike Rental", "Inter-city Bus"
        ],
        "keywords": ["uber", "ola", "rapido", "irctc", "fuel", "petrol", "diesel",
                     "parking", "toll", "redbus", "makemytrip", "indigo", "spicejet"]
    },
    "Utilities & Bills": {
        "subcategories": [
            "Electricity", "Water", "Gas (PNG/LPG)", "Internet & Broadband",
            "Mobile Recharge", "DTH & Cable TV", "Landline",
            "Piped Water", "Society Maintenance"
        ],
        "keywords": ["electricity", "power", "water", "gas", "internet", "broadband",
                     "recharge", "dth", "cable", "tata sky", "airtel", "jio", "bsnl",
                     "bescom", "mseb", "uppcl", "tneb"]
    },
    "Healthcare": {
        "subcategories": [
            "Hospitals & Clinics", "Pharmacy", "Diagnostic Labs",
            "Doctor Consultation", "Dental", "Optical",
            "Ayurveda & Alternative Medicine", "Mental Health", "Insurance Premium"
        ],
        "keywords": ["hospital", "clinic", "pharmacy", "medical", "health", "doctor",
                     "lab", "diagnostic", "apollo", "1mg", "pharmeasy", "lybrate",
                     "practo", "ayush", "dental", "optical"]
    },
    "Entertainment": {
        "subcategories": [
            "Movies & Cinema", "OTT Subscriptions", "Gaming",
            "Music & Concerts", "Theme Parks", "Sports Events",
            "Stand-up Comedy", "Clubs & Nightlife"
        ],
        "keywords": ["pvr", "inox", "bookmyshow", "netflix", "hotstar", "prime",
                     "spotify", "gaana", "zee5", "sony", "youtube", "gaming"]
    },
    "Education": {
        "subcategories": [
            "School Fees", "College Fees", "Online Courses",
            "Coaching & Tuitions", "Books & Study Material",
            "Skill Development", "Certifications"
        ],
        "keywords": ["school", "college", "university", "udemy", "coursera",
                     "byju", "unacademy", "vedantu", "whitehat", "upgrad",
                     "coaching", "tuition", "fees", "admission"]
    },
    "Financial Services": {
        "subcategories": [
            "Loan EMI", "Credit Card Payment", "Insurance Premium",
            "Mutual Funds", "Stock Broking", "Fixed Deposits",
            "Gold Purchase", "Crypto", "UPI Transfer"
        ],
        "keywords": ["emi", "loan", "insurance", "mutual fund", "zerodha", "groww",
                     "upstox", "angel", "lici", "hdfc life", "bajaj", "sbi",
                     "icici", "axis", "kotak", "sip", "ppf"]
    },
    "Travel & Accommodation": {
        "subcategories": [
            "Hotels & Resorts", "Hostels", "Airbnb & Home Stays",
            "Flight Tickets", "Tour Packages", "Visa & Documentation",
            "Travel Insurance", "Luggage"
        ],
        "keywords": ["hotel", "resort", "airbnb", "oyo", "treebo", "fabhotel",
                     "makemytrip", "goibibo", "yatra", "thomas cook", "clearing",
                     "hostel", "homestay", "flight", "tour"]
    },
    "Personal Care": {
        "subcategories": [
            "Salon & Spa", "Gym & Fitness", "Yoga & Wellness",
            "Beauty & Cosmetics", "Laundry", "Tailoring"
        ],
        "keywords": ["salon", "spa", "beauty", "gym", "fitness", "yoga",
                     "laundry", "tailor", "nykaa", "purplle", "urbanclap",
                     "housejoy", "urbane", "ustraa"]
    },
    "Home & Maintenance": {
        "subcategories": [
            "Rent", "Society Charges", "Housekeeping",
            "Plumbing & Electrical Repairs", "Furniture & Decor",
            "Pest Control", "Interior Design", "Property Tax"
        ],
        "keywords": ["rent", "society", "maintenance", "plumber", "electrician",
                     "carpenter", "pest", "interior", "painting", "nobroker",
                     "magicbricks", "housing", "99acres"]
    },
    "Subscriptions & Memberships": {
        "subcategories": [
            "OTT Platforms", "Music Streaming", "News & Magazines",
            "Cloud Storage", "Software & SaaS", "Professional Memberships",
            "Gaming Subscriptions"
        ],
        "keywords": ["subscription", "premium", "pro", "plus", "membership",
                     "annual", "monthly plan", "renew", "auto-renewal"]
    },
    "Transfers & Payments": {
        "subcategories": [
            "UPI Peer Transfer", "Bank Transfer", "Wallet Top-up",
            "Loan Repayment to Individual", "Rent to Individual",
            "Freelance Payment Received"
        ],
        "keywords": ["upi", "neft", "imps", "transfer", "send money", "wallet",
                     "paytm", "phonepe", "gpay", "bhim", "cred"]
    },
    "Government & Taxes": {
        "subcategories": [
            "Income Tax", "GST Payment", "Property Tax",
            "Vehicle Tax", "Passport & Visa Fees",
            "Municipal Corporation", "Traffic Fine"
        ],
        "keywords": ["tax", "gst", "income tax", "tds", "mcd", "bmc", "bbmp",
                     "passport", "challan", "fine", "government", "e-challan"]
    },
    "Charity & Donations": {
        "subcategories": [
            "NGO & Nonprofit", "Religious Donations",
            "Crowdfunding", "Political Donations"
        ],
        "keywords": ["donation", "charity", "ngo", "temple", "mosque", "church",
                     "gurudwara", "zakat", "tithe", "trust", "foundation"]
    },
}

# Flat list of all subcategories
ALL_SUBCATEGORIES = []
for cat, data in CATEGORY_TAXONOMY.items():
    for subcat in data["subcategories"]:
        ALL_SUBCATEGORIES.append(f"{cat} > {subcat}")

# Category aliases for fuzzy matching
CATEGORY_ALIASES = {
    "food": "Food & Dining",
    "eating": "Food & Dining",
    "groceries": "Food & Dining > Groceries",
    "transport": "Transportation",
    "travel local": "Transportation",
    "bills": "Utilities & Bills",
    "utilities": "Utilities & Bills",
    "medical": "Healthcare",
    "medicine": "Healthcare > Pharmacy",
    "investment": "Financial Services",
    "ott": "Entertainment > OTT Subscriptions",
    "streaming": "Entertainment > OTT Subscriptions",
    "gym": "Personal Care > Gym & Fitness",
    "rent": "Home & Maintenance > Rent",
}