from statements.llm_fallback import (
    parse_bank_statement_with_llm,
    categorize_transaction_with_llm,
)


if __name__ == "__main__":
    # Test 1: categorization
    result = categorize_transaction_with_llm("UPI/9876543210/Rahul sharma/payment")
    print("Categorization test:", result)

    # Test 2: P2P detection
    result2 = categorize_transaction_with_llm("SWIGGY FOOD ORDER BANGALORE")
    print("Merchant test:", result2)

    # Test 3: statement parsing (paste a few lines from a real statement)
    sample = """
10/01/2024  UPI-SWIGGY-9876@okaxis  Dr  450.00  12,550.00
11/01/2024  SALARY CREDIT INFOSYS   Cr  85000.00  97,550.00
12/01/2024  UPI-9988776655-RAHUL    Dr  2000.00  95,550.00
"""

    transactions = parse_bank_statement_with_llm(sample)
    print("Parsed transactions:", transactions)

