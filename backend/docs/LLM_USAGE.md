# Where the LLM (DeepSeek / Gemini) is used

This document lists every code path that calls the LLM APIs. The app supports **DeepSeek** (primary) and **Gemini** (optional for chunked work). Chunked processing: **split data → run LLM on each chunk → merge output** to keep accuracy while reducing per-call latency.

---

## 1. **Assistant routes** (`assistant/routes.py`)

All of these use `ask()` from `assistant/llm_service.py` (one DeepSeek call per request):

| Endpoint | What it does | LLM call |
|----------|----------------|----------|
| `POST /assistant/query` | Answer a natural-language question about the user's transactions | 1× `ask(prompt, max_tokens=1024)` |
| `GET /assistant/report?month=YYYY-MM` | Generate a written monthly financial report | 1× `ask(prompt, max_tokens=1024)` |
| `POST /assistant/budget` | Generate a suggested monthly budget (JSON) | 1× `ask(prompt, max_tokens=1024)` |
| `POST /assistant/anomaly/explain` | Explain an unusual transaction | 1× `ask(prompt, max_tokens=512)` |
| `POST /assistant/loan/upload` | Extract key terms from a loan PDF | 1× `ask(prompt, max_tokens=1024)` |
| `GET /assistant/tax/suggestions` | Suggest tax-saving opportunities from transaction history | 1× `ask(prompt, max_tokens=1024)` |
| `GET /assistant/income-advice?month=...` | Investment/savings advice based on income vs spend | 1× `ask(prompt, max_tokens=1024)` |

---

## 2. **Statement PDF analysis** (`statements/routes.py`)

| Step | What it does | LLM usage |
|------|----------------|-----------|
| **Parse PDF text** | When table/regex parsing finds few rows (< 3 and text > 500 chars), fallback parser runs. | If text length ≤ 40k chars: 1× `parse_bank_statement_with_llm(text)`. If **long** (> 40k): **chunked** — text is split into chunks (~35k chars), each chunk is parsed with **Gemini or DeepSeek**, then results are merged and deduped. |
| **Categorize each row** | After parsing, every transaction is categorized. | Uses ML + merchant DB only (no per-row LLM) for speed. |

So for a long PDF you get **one LLM call per chunk** (Gemini preferred when `GEMINI_API_KEY` is set), not one per transaction.

---

## 3. **Categorization** (`categorization/routes.py` + `smart_categorization`)

| Endpoint / flow | LLM usage |
|------------------|-----------|
| `POST /categorize` (single transaction) | LLM **can** be used as fallback when ML confidence is below threshold (`ML_LOW_CONF_THRESHOLD`, default 0.70). `enable_llm_fallback=True` by default. |
| `POST /categorize/batch` | By default: LLM **disabled** (merchant DB + ML only). If you send **`use_llm_chunked: true`** in the JSON body and either **Gemini or DeepSeek** is configured: transactions are **split into chunks** (default 15 per chunk), each chunk is sent to the LLM in one request, then results are merged and enrichment (P2P, merchant, tags) is applied. Uses **Gemini** when `GEMINI_API_KEY` is set, else **DeepSeek**. |
| `POST /categorize/sms` | Same as single: LLM fallback **enabled** when ML is unsure. |

---

## 4. **Smart categorization engine** (`smart_categorization/core/categorizer.py`)

- **LLM categorizer** (`llm_categorizer.py`) uses `OllamaClient` (DeepSeek under the hood).
- It is invoked when:
  - `use_llm_only=True` (e.g. PDF flow – now we set `enable_llm_fallback=False` for PDF categorization so this path is no longer used for PDF rows), or
  - `enable_llm_fallback=True` and ML confidence < threshold and no merchant DB match → one `llm.categorize(description, amount)` per transaction.

---

## 5. **Statement LLM fallback module** (`statements/llm_fallback.py`)

| Function | Used by | Purpose |
|----------|---------|---------|
| `parse_bank_statement_with_llm(raw_text)` | `statements/routes.py` (PDF analyze) | Single call to extract list of transactions from raw statement text when regex/table parsing is weak. |
| `categorize_transaction_with_llm(narration)` | Not used by the main app; only by `test_groq.py` | Categorize a single narration via LLM. |

---

## Summary: what is still using the LLM?

- **Assistant:** all 7 endpoints above (1 call per request; DeepSeek).
- **PDF analyze:** when regex finds few rows, **parse** uses LLM — **chunked** when text > 40k chars (Gemini or DeepSeek per chunk); categorization of rows uses ML + DB only.
- **Single transaction / SMS:** LLM used only as fallback when ML confidence is low and no merchant match.
- **Batch categorization:** no LLM by default. With **`use_llm_chunked: true`** and Gemini or DeepSeek configured: **chunked** (e.g. 15 txns per API call), then merge.

## Adding Gemini

Set in `backend/.env`:

- `GEMINI_API_KEY=your-api-key` — get one from Google AI Studio.
- Optional: `GEMINI_MODEL=gemini-1.5-flash` (default).

When `GEMINI_API_KEY` is set, **chunked** operations (long PDF parse, batch categorize with `use_llm_chunked: true`) use **Gemini**; otherwise they use **DeepSeek**. Assistant endpoints (query, report, budget, etc.) continue to use **DeepSeek** only.
