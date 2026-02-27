## Personal Expense Tracker

Smart, India‑focused personal expense tracker with:
- **Bank statement ingestion** (UCO, SBI, HDFC, Axis, ICICI, Kotak, PhonePe, SMS)
- **Smart categorization engine** (ML + rules + feedback learning)
- **Rich P2P detection** (UPI/NEFT/IMPS, direction, relationship)

---

## 🔧 Prerequisites

- **Python** 3.10+
- **Node.js** 18+ and **npm**
- **Git** (for cloning)

---

## 🚀 Clone the repo

```bash
git clone https://github.com/<your-username>/personal-expense-tracker.git
cd personal-expense-tracker
```

Replace `<your-username>` with your GitHub username.

---

## 🐍 Backend setup

From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the virtualenv:

- **Windows (PowerShell)**:

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

- **macOS/Linux**:

  ```bash
  source .venv/bin/activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the `backend` folder (minimal example):

```bash
ENV=local
SECRET_KEY=change-me
DEBUG=True
```

Run the backend (adjust if your entry file is different):

```bash
python app.py
```

---

## 🧠 Smart Categorization notebook

The demo notebook lives at `backend/smart_categorization/Smart_Categorization_India.ipynb`.

1. Open the notebook in VS Code / Jupyter.
2. Select the **.venv** interpreter you created above.
3. Run all cells to:
   - Initialize `SmartCategorizationPipeline`.
   - See sample Indian transactions categorized.
   - Inspect P2P labels like **“UPI Sent – Friends & Family”**, **“NEFT Received – Salary”**.

---

## 📥 Parsing bank statements

Use the multi‑bank parser + pipeline to process CSV/Excel statements:

```python
from backend.statements.bank_parser import load_and_parse
from backend.smart_categorization.core.pipeline import SmartCategorizationPipeline

# 1. Parse any supported bank statement
parsed = load_and_parse("path/to/statement.csv")  # auto-detects bank from headers

# 2. Initialize pipeline
pipeline = SmartCategorizationPipeline()

# 3. Run full categorization + P2P detection
results = [
    pipeline.process(p.to_pipeline_transaction())
    for p in parsed
]

# Each 'results[i]' contains:
# - category, subcategory
# - is_p2p, p2p_direction, p2p_counterparty, p2p_confidence
# - merchant enrichment, tags, etc.
```

For Excel files (`.xlsx`/`.xls`), `load_and_parse("file.xlsx")` works the same way.

---

## 🌐 Frontend (if present)

If this repo has a `frontend` folder:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in the terminal (typically `http://localhost:5173`).

---

## ✅ Quick checklist

- [ ] Clone repo and `cd` into it
- [ ] Create & activate Python virtualenv in `backend`
- [ ] `pip install -r requirements.txt`
- [ ] Create `backend/.env`
- [ ] Run `python app.py`
- [ ] (Optional) Run the notebook `Smart_Categorization_India.ipynb`
- [ ] (Optional) Start frontend with `npm run dev`
