# Sample data for FinSight uploads

Use these files to test each upload type in the app.

---

## 1. Batch (CSV) — Categorize → Batch (CSV) tab

**File:** `sample_transactions.csv`

- **Headers required:** `transaction_id`, `date`, `description`, `amount`
- **Alternate headers accepted:** `id` (for transaction_id), `txn_date`/`transaction_date` (for date), `narration`/`remarks` (for description), `debit`/`value` (for amount)
- Upload this file or paste its contents into the CSV text area, then click **Categorize**.

---

## 2. Bank SMS — Categorize → Bank SMS tab

**Files:** `sample_sms_hdfc.txt`, `sample_sms_sbi.txt`

- **HDFC:** Paste one line like: `HDFC Bank: Rs.450.00 debited from A/c XX1234 on 15-Jan-24 to VPA ZOMATO@ICICI Ref No 456789`
- **SBI:** Paste one line like: `SBI: Your A/c XX5678 is debited by Rs.1,200.00 on 16/01/24 to BIGBASKET ORDER.`
- Select bank (HDFC or SBI), paste the SMS text, then click **Categorize**.

---

## 3. Line items (split) — Categorize → Line items (split) tab

**File:** `sample_line_items.json`

- Use for a single transaction that you want to split into multiple line items (e.g. one Amazon order with several products).
- In the form: set **Transaction id**, **Date**, **Description**, **Amount** (total), and paste the contents of `sample_line_items.json` into the **Line items (JSON)** field.
- Example: transaction_id `T100`, date `2024-01-18`, description `AMAZON PAY PURCHASE`, amount `4599`, line_items = content of `sample_line_items.json`.

---

## 4. Raw transaction — Categorize → Raw transaction tab

- No file. Fill in: **Transaction id** (e.g. `T001`), **Date** (e.g. `2024-01-15`), **Description** (e.g. `ZOMATO ORDER #789456`), **Amount** (e.g. `450`), then click **Categorize**.

---

## 5. PDF bank statement — Categorize → PDF statement tab

- **Format:** Any text-based PDF bank statement (e.g. downloaded from HDFC/SBI/ICICI/Axis or generic).
- **Optional:** Set **Bank** (generic | hdfc | sbi | icici | axis) and **Max pages**.
- Upload the PDF and click **Analyze**. The app will extract transactions and categorize them.

---

## 6. Loan document (PDF) — Assistant → Loan Document Analyzer

- **Format:** Loan sanction letter or agreement PDF (e.g. home loan, personal loan).
- Upload the PDF; the app will extract principal, EMI, tenure, interest rate, lender, sanction date, prepayment clause, etc.
