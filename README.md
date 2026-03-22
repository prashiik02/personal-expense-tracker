# Personal Expense Tracker

Smart, India-focused personal expense tracker with:

- **Bank statement ingestion** — PDF statements, CSV/Excel exports, bank SMS (HDFC, SBI)
- **Multi-bank CSV parser** — UCO, SBI, HDFC, Axis, ICICI, Kotak, PhonePe
- **Smart categorization** — ML + rules + merchant DB, with optional LLM fallback (DeepSeek / Gemini)
- **P2P detection** — UPI/NEFT/IMPS, direction, counterparty
- **AI assistant** — Chat, monthly reports, budget suggestions, loan PDF parsing, tax tips, anomaly explainer
- **React + Vite frontend** — Dashboard, Categorize, Assistant pages with charts and dark mode

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ and **npm**
- **Git** (for cloning)

---

## Quick start

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/personal-expense-tracker.git
cd personal-expense-tracker
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
```

Activate the virtualenv:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS/Linux:** `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `backend/.env` (copy from the template):

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` and set at least:

```env
SECRET_KEY=change-me-to-a-secret
JWT_SECRET_KEY=change-me-to-a-secret
```

#### Database (SQLite by default)

If you **do not** set `SQLALCHEMY_DATABASE_URI`, the app uses **SQLite** at:

| Path | Description |
|------|-------------|
| **`backend/instance/auth_app.db`** | Default SQLite file (the `instance` folder is created automatically) |

For **MySQL**, set all of `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` in `.env` (and do not set `SQLALCHEMY_DATABASE_URI`), or set `SQLALCHEMY_DATABASE_URI` explicitly to your connection string.

**Migrating an old SQLite file:** If you previously used `expense_tracker.db` or `auth_app.db` in the repo root, copy that file to `backend/instance/auth_app.db` (or point `SQLALCHEMY_DATABASE_URI` at the old path).

Run the backend:

```bash
python app.py
```

Backend runs at `http://127.0.0.1:5000`.

### 3. Frontend setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at **`http://localhost:5173`** (Vite may use **5174** if 5173 is busy).

### 4. Use the app

1. Open the frontend URL (e.g. `http://localhost:5173`)
2. **Register** (name, email, password, monthly income in INR)
3. **Login**
4. **Dashboard** — view spending analytics and charts
5. **Categorize** — add transactions via raw input, bank SMS, batch CSV, or PDF statement
6. **Assistant** — chat, reports, budget, tax tips, loan PDFs

---

## LLM configuration (optional)

The app uses **DeepSeek** (primary) and **Gemini** (optional for batch/chunked work). Assistant features (chat, reports, budget, etc.) require **DeepSeek**.

### DeepSeek (required for Assistant)

1. Get an API key from [DeepSeek Console](https://platform.deepseek.com/).
2. Add to `backend/.env`:

```env
DEEPSEEK_API_KEY=your-deepseek-api-key-here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### Gemini (optional — for batch categorization and long PDFs)

1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Add to `backend/.env`:

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash
```

When `GEMINI_API_KEY` is set, chunked operations (batch categorize with `use_llm_chunked: true`, long PDF parsing) can use Gemini; otherwise they use DeepSeek.

### Transaction categorization LLM (optional)

Single-transaction / SMS fallback uses DeepSeek JSON mode when ML confidence is low. Set:

```env
LLM_CATEGORIZATION_ENABLED=true
LLM_MIN_CONFIDENCE=0.62
```

See `backend/docs/LLM_USAGE.md` for details.

---

## API overview

### Auth

- `POST /auth/register` — `{ name, email, password, monthly_income }`
- `POST /auth/login` — `{ email, password }` → returns `{ user, token }`

All other endpoints require `Authorization: Bearer <token>`.

### Statements

- `POST /statements/analyze` — Upload PDF statement (form: `file`, optional `bank`, `max_pages`)
- `GET /statements/dashboard` — Aggregated analytics for the user
- `GET /statements/transactions` — List transactions (query: `category`, `subcategory`, `month`, `limit`)
- `PATCH /statements/transactions/<id>` — Update category or exclude from analytics

### Categorization

- `POST /categorize` — Single transaction
- `POST /categorize/batch` — Batch or CSV (`transactions` or `csv_text`, optional `use_llm_chunked`)
- `POST /categorize/sms` — Bank SMS (`sms_text`, `bank`: `hdfc` | `sbi`)
- `POST /categorize/correction` — Record a correction for learning

### Assistant

- `POST /assistant/query` — `{ "question": "..." }` — Chat about your transactions
- `GET /assistant/report?month=YYYY-MM` — Monthly financial report
- `POST /assistant/budget` — Generate suggested budget (stored in `budget_suggestions`)
- `POST /assistant/anomaly/explain` — `{ "transaction_id": 123 }` or `{ "details": {...} }`
- `POST /assistant/loan/upload` — Upload loan PDF (form: `file`)
- `GET /assistant/tax/suggestions` — Tax-saving tips from spending
- `GET /assistant/income-advice?month=YYYY-MM` — Investment/savings advice vs spend
- `POST /assistant/whatsapp-sms` — Parse WhatsApp-forwarded bank SMS

---

## Programmatic bank statement parsing

For CSV/Excel files, use the bank parser directly:

```python
import sys
sys.path.insert(0, "backend")  # if running from project root

from statements.bank_parser import load_and_parse
from smart_categorization.core.pipeline import SmartCategorizationPipeline

# Parse any supported bank statement (auto-detects bank from headers)
parsed = load_and_parse("path/to/statement.csv")

# Or for Excel
parsed = load_and_parse("path/to/statement.xlsx")

# Initialize pipeline and categorize
pipeline = SmartCategorizationPipeline()
results = [
    pipeline.process(p.to_pipeline_transaction())
    for p in parsed
]

# Each result has: category, subcategory, is_p2p, p2p_direction, p2p_counterparty, merchant, tags, etc.
```

Supported banks: UCO, SBI, HDFC, Axis, ICICI, Kotak, PhonePe.

---

## Smart categorization notebook

Demo notebook: `backend/smart_categorization/Smart_Categorization_India.ipynb`

1. Open in VS Code or Jupyter
2. Select the `.venv` interpreter from `backend/`
3. Run all cells to see sample Indian transactions categorized, P2P labels, and pipeline behavior

---

## Project structure

```
personal-expense-tracker/
├── backend/
│   ├── app.py              # Flask app entry
│   ├── config.py           # Config (DB, JWT, env)
│   ├── requirements.txt
│   ├── .env.example        # Template for secrets (copy to .env)
│   ├── instance/           # SQLite default: auth_app.db (created on first run)
│   ├── auth/               # Register, login
│   ├── categorization/     # Single, batch, SMS
│   ├── statements/         # PDF analyze, dashboard
│   ├── assistant/          # LLM-backed features
│   ├── models/             # User, Transaction, LoanDocument, BudgetSuggestion, AnomalyRecord
│   ├── smart_categorization/  # Pipeline, ML, merchant DB, P2P, DeepSeek JSON client
│   └── llm_providers.py    # DeepSeek + Gemini (chunked)
├── frontend/
│   ├── src/
│   │   ├── pages/          # Dashboard, Categorize, Assistant, Login, Register
│   │   ├── components/     # Charts, forms, cards
│   │   ├── api/            # API client
│   │   └── context/        # Auth, Theme
│   └── package.json
├── upload/                 # Sample CSV/SMS/PDF for testing
└── README.md
```

---

## Manual LLM smoke test

From `backend/` with `DEEPSEEK_API_KEY` set:

```bash
python test_llm_fallback.py
```

---

## Checklist

- [ ] Clone repo and `cd` into it
- [ ] Create and activate Python venv in `backend`
- [ ] `pip install -r requirements.txt`
- [ ] Copy `backend/.env.example` to `backend/.env` and set `SECRET_KEY`, `JWT_SECRET_KEY`
- [ ] (Optional) Add `DEEPSEEK_API_KEY` for Assistant features
- [ ] Run backend: `cd backend && python app.py`
- [ ] Run frontend: `cd frontend && npm run dev`
- [ ] Register and login at the frontend URL
- [ ] (Optional) Run notebook `Smart_Categorization_India.ipynb`
