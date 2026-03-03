# Flask Backend for SMS Transactions

This simple Flask service accepts a list of parsed transactions from the
Android client, verifies the JWT of the requester, encrypts sensitive
data using Fernet (AES) and stores the result in MongoDB.

## Setup

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in real secrets. The file should contain:

   ```env
   JWT_SECRET_KEY=your-jwt-secret
   FERNET_KEY=base64-32-byte-key
   # MongoDB connection string from Atlas (include username and password):
   # e.g. mongodb+srv://user:pass@fintechcluster.7yexyva.mongodb.net/expenseDB
   MONGO_URI=your-atlas-connection-string
   DB_NAME=expenseDB
   COLLECTION_NAME=transactions
   ```

   If your Atlas URI looks like `1HlS80F8Nms471j9@fintechcluster.7yexyva.mongodb.net/?appName=fintechcluster` then prepend
   `mongodb+srv://<username>:<password>@` and append the database name, e.g.
   `mongodb+srv://user:pwd@fintechcluster.7yexyva.mongodb.net/expenseDB?appName=fintechcluster`.

### Google login support

The server exposes a `/login-google` endpoint that accepts a JSON body with
`{"id_token": "<Google ID token>"}`. You must register a web client ID in
the Google Cloud Console and request that ID token from your Android client.

A successful login returns:

```json
{"access_token": "<JWT>"}
```

Use this JWT for subsequent requests to protected routes such as
`/sync-transactions`.


   You can generate a Fernet key in Python with:
   ```py
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```

3. Run the server:
   ```powershell
   python app.py
   ```

   In production use a WSGI server and HTTPS.

## API

`POST /sync-transactions` – requires `Authorization: Bearer <JWT>` header and
JSON body containing an array of transaction objects:

```json
[
  {"amount": 500, "merchant": "Amazon", "type": "debit", "date": "2026-02-27"}
]
```

Only the encrypted fields are persisted; raw SMS text is never logged or
stored.

`GET /transactions` – authenticated route that returns the decrypted
transactions belonging to the JWT's user. The response is a list of the same
objects sent by the Android app.

`POST /ai-insights` – proxy endpoint for conversational AI. Body should be
`{"prompt":"..."}` and the server will forward the request to the
configured AI provider using the API key stored in `AI_API_KEY`.

Environment configuration:

* `AI_API_KEY` – your API key for the chosen model service.
* `AI_PROVIDER` – either `anthropic` (default) or `gemini`.
* `AI_ENDPOINT` – optional custom endpoint for Gemini (defaults to
  `text-bison-001` generate URL).

**Example Gemini URI** (use with `AI_PROVIDER=gemini`):

```env
AI_API_KEY=your_google_cloud_key
AI_PROVIDER=gemini
AI_ENDPOINT=https://generativemodels.googleapis.com/v1/models/text-bison-001:generate
```

The backend determines which code path to take based on `AI_PROVIDER` and
returns `{ "text": "..." }` in either case.

`GET /loan-suggestions` – provides personalized loan/EMI suggestions based on user's financial transactions. Uses transaction history to calculate:
- Monthly income
- Monthly expenses
- Monthly savings
- Affordable max loan
- EMI options at different interest rates (5–15%)

Query parameters (optional):
- `tenure_months`: loan duration (default 60)
- `min_rate`: minimum interest rate % (default 5)
- `max_rate`: maximum interest rate % (default 15)

Requires `Authorization: Bearer <JWT>` header.

`POST /emi-calculator` – direct EMI calculator. Body:

```json
{
  "principal": 500000,
  "annual_interest_rate": 10,
  "tenure_months": 60
}
```

Returns exact monthly EMI, total interest, and repayment breakdown.

Cross‑origin requests are allowed by default (Flask‑CORS) so you can host the
React frontend on a different port during development.
