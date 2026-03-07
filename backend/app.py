from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from pymongo import MongoClient
from cryptography.fernet import Fernet
from config import JWT_SECRET_KEY, FERNET_KEY, MONGO_URI, DB_NAME, COLLECTION_NAME

# add google auth imports
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# CORS support for local development
from flask_cors import CORS
import os
import requests as http_requests
import yfinance as yf

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
CORS(app)  # allow cross-origin requests
jwt = JWTManager(app)

# MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
users_collection = db.get_collection("users")  # store minimal user info

# FERNET_KEY is already a base64-encoded string from .env/config
if isinstance(FERNET_KEY, str):
    cipher = Fernet(FERNET_KEY.encode())
else:
    cipher = Fernet(FERNET_KEY)

# Health check endpoint (required for Render)
@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - used by Render to verify app is running.
    Returns 200 if app is operational, 500 if MongoDB is unavailable.
    """
    try:
        # Quick MongoDB connectivity check
        db.command('ping')
        return jsonify({'status': 'healthy', 'service': 'expense-backend'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route("/sync-transactions", methods=["POST"])
@jwt_required()
def sync_transactions():
    user_id = get_jwt_identity()
    transactions = request.get_json(force=True)

    if not isinstance(transactions, list):
        return jsonify({"error": "Expected a list of transactions"}), 400

    for txn in transactions:
        # basic validation
        if not all(k in txn for k in ("amount", "merchant", "type", "date")):
            continue

        encrypted_amount = cipher.encrypt(str(txn["amount"]).encode()).decode()
        encrypted_merchant = cipher.encrypt(txn["merchant"].encode()).decode()
        encrypted_account = None
        if txn.get("account"):
            encrypted_account = cipher.encrypt(str(txn["account"]).encode()).decode()

        doc = {
            "user_id": user_id,
            "encrypted_amount": encrypted_amount,
            "encrypted_merchant": encrypted_merchant,
            "type": txn["type"],
            "date": txn["date"]
        }
        if encrypted_account:
            doc["encrypted_account"] = encrypted_account

        collection.insert_one(doc)

    return jsonify({"message": "Transactions stored securely"}), 200

# simple Google OAuth2 login endpoint
@app.route('/login-google', methods=['POST'])
def login_google():
    data = request.get_json(force=True)
    token = data.get('id_token')
    if not token:
        return jsonify({'error': 'Missing id_token'}), 400

    try:
        # verify the token with Google
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
        # idinfo contains fields such as 'sub' (user id), 'email'
        google_user_id = idinfo['sub']
        email = idinfo.get('email')
    except ValueError:
        return jsonify({'error': 'Invalid token'}), 400

    # create or get user record
    user = users_collection.find_one({'google_id': google_user_id})
    if not user:
        user = {
            'google_id': google_user_id,
            'email': email,
        }
        users_collection.insert_one(user)

    # create JWT using google_user_id as identity
    access_token = create_access_token(identity=google_user_id)
    return jsonify({'access_token': access_token}), 200


# return decrypted transactions for the current user
@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    docs = list(collection.find({'user_id': user_id}))
    result = []
    for d in docs:
        try:
            amt = cipher.decrypt(d['encrypted_amount'].encode()).decode()
            merch = cipher.decrypt(d['encrypted_merchant'].encode()).decode()
            account = None
            if d.get('encrypted_account'):
                account = cipher.decrypt(d['encrypted_account'].encode()).decode()
        except Exception:
            continue
        result.append({
            'amount': float(amt),
            'merchant': merch,
            'type': d.get('type'),
            'date': d.get('date'),
            'account': account
        })
    return jsonify(result), 200


# proxy to AI service (Anthropic/Gemini etc.)
@app.route('/ai-insights', methods=['POST'])
@jwt_required()
def ai_insights():
    payload = request.get_json(force=True)
    prompt = payload.get('prompt')
    if not prompt:
        return jsonify({'error': 'Missing prompt'}), 400
    # Get logged - in user
    user_id = get_jwt_identity()
    
    docs = list(collection.find({'user_id': user_id}).limit(50))
    transactions = []

    for d in docs[:50]:
        try:
            amt = cipher.decrypt(d['encrypted_amount'].encode()).decode()
            merch = cipher.decrypt(d['encrypted_merchant'].encode()).decode()
            transactions.append({
                "amount": float(amt),
                "merchant": merch,
                "type": d.get("type"),
                "date": d.get("date")
            })
        except Exception:
            continue

    # get user's financial profile
    profile = get_user_financial_profile(user_id)

    # Build AI context using financial data
    
    context_prompt = f"""
    You are a financial advisor AI.

    User financial profile:
    Monthly income: {profile['monthly_income']}
    Monthly expenses: {profile['monthly_expenses']}
    Monthly savings: {profile['monthly_savings']}
    Affordable EMI: {profile['affordable_monthly_emi']}
    Recommended maximum loan: {profile['recommended_max_loan']}

    Recent transactions:
    {transactions}

    User question:
    {prompt}

    Give:
    1. Spending insights
    2. Saving recommendations
    3. Budget improvement suggestions
    4. Loan advice based on affordability
    """
    
# AI insights endpoint - proxies to Anthropic/Gemini based on configuration

    ai_key = os.getenv('AI_API_KEY')
    if not ai_key:
        return jsonify({'error': 'AI_API_KEY not configured'}), 500

    provider = os.getenv('AI_PROVIDER', 'anthropic').lower()
    try:
        if provider == 'gemini':
            # Gemini / Google Generative Models example
            # documentation: https://developers.generativeai.google/api/rest
            endpoint = os.getenv('AI_ENDPOINT', 'https://generativemodels.googleapis.com/v1/models/text-bison-001:generate')
            resp = http_requests.post(
                endpoint,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {ai_key}'
                },
                json={
                    'prompt': context_prompt,
                    'maxOutputTokens': 800
                },
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            # Google Generative API response format: candidates[].content.parts[].text
            try:
                text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            except (IndexError, KeyError, TypeError):
                # fallback if response format is unexpected
                text = data.get('candidates', [{}])[0].get('output', '')
        else:
            # default to Anthropic
            resp = http_requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': ai_key,
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': 'claude-sonnet-4-20250514',
                    'max_tokens': 800,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                },
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
            # Anthropic response format: content[].text
            try:
                text = data.get('content', [{}])[0].get('text', '')
            except (IndexError, KeyError, TypeError):
                text = ''
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'text': text}), 200




# ═══════════════════════════════════════════════════════════
# EMI & LOAN SUGGESTION ENDPOINTS
# ═══════════════════════════════════════════════════════════

def calculate_emi(principal, annual_rate, tenure_months):
    """
    Calculate EMI using the formula:
    EMI = P * [{r*(1+r)^n} / {(1+r)^n - 1}]
    where:
      P = Principal (loan amount)
      r = Monthly interest rate (annual_rate/12/100)
      n = Tenure in months
    """
    if principal <= 0 or tenure_months <= 0:
        return 0
    if annual_rate == 0:
        return principal / tenure_months
    
    monthly_rate = annual_rate / 12 / 100
    numerator = monthly_rate * ((1 + monthly_rate) ** tenure_months)
    denominator = ((1 + monthly_rate) ** tenure_months) - 1
    emi = principal * (numerator / denominator)
    return round(emi, 2)


def get_user_financial_profile(user_id):
    """
    Analyze user's transactions to determine:
    - Monthly average income
    - Monthly average expenses
    - Monthly savings
    - Recommended max loan based on affordability
    """
    docs = list(collection.find({'user_id': user_id}))
    if not docs:
        return {
            'monthly_income': 0,
            'monthly_expenses': 0,
            'monthly_savings': 0,
            'recommended_max_loan': 0,
            'affordable_monthly_emi': 0
        }
    
    # Decrypt and categorize transactions
    income_total = 0
    expense_total = 0
    months_tracked = set()
    
    for d in docs:
        try:
            amt = float(cipher.decrypt(d['encrypted_amount'].encode()).decode())
            txn_type = d.get('type')
            txn_date = d.get('date', '')[:7]  # YYYY-MM
            months_tracked.add(txn_date)
            
            if txn_type == 'income':
                income_total += amt
            elif txn_type == 'debit':
                expense_total += amt
        except Exception:
            continue
    
    num_months = max(len(months_tracked), 1)
    monthly_income = round(income_total / num_months, 2)
    monthly_expenses = round(expense_total / num_months, 2)
    monthly_savings = round(monthly_income - monthly_expenses, 2)
    
    # Assume user can afford EMI up to 40% of monthly savings
    # Recommended max loan = (affordable_monthly_emi * tenure_months) / EMI factor
    affordable_monthly_emi = round(monthly_savings * 0.4, 2)
    
    # Conservative estimate: for 60-month tenure at 10% interest,
    # max principal ≈ affordable_emi * 17.5 (rough multiplier)
    recommended_max_loan = round(affordable_monthly_emi * 17.5, 0)
    
    return {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'affordable_monthly_emi': affordable_monthly_emi,
        'recommended_max_loan': recommended_max_loan,
        'months_analyzed': num_months
    }

# ─────────────────────────────────────────────
# STOCK MARKET SIGNAL
# ─────────────────────────────────────────────
def get_stock_signal(symbol="TCS.NS"):
    stock = yf.Ticker(symbol)

    data = stock.history(period="1mo")

    current_price = data["Close"].iloc[-1]
    avg_price = data["Close"].mean()

    suggestion = "Bullish" if current_price > avg_price else "Bearish"

    return {
        "symbol": symbol,
        "current_price": float(current_price),
        "average_price": float(avg_price),
        "signal": suggestion
    }


@app.route('/loan-suggestions', methods=['GET'])
@jwt_required()
# ─────────────────────────────────────────────
# STOCK SIGNAL ENDPOINT
# ─────────────────────────────────────────────
@app.route('/stock-signal', methods=['GET'])
@jwt_required()
def stock_signal():
    symbol = request.args.get("symbol", "TCS.NS")
    result = get_stock_signal(symbol)
    return jsonify(result), 200

def loan_suggestions():
    """
    Provide loan/EMI suggestions based on user's financial profile.
    Query params:
      - tenure_months: default 60 (5 years)
      - min_rate: default 5 (interest rate %)
      - max_rate: default 15 (interest rate %)
    Returns array of EMI suggestions for different loan amounts.
    """
    user_id = get_jwt_identity()
    
    # Get query parameters
    tenure = int(request.args.get('tenure_months', 60))
    min_rate = float(request.args.get('min_rate', 5))
    max_rate = float(request.args.get('max_rate', 15))
    
    profile = get_user_financial_profile(user_id)
    
    if profile['monthly_savings'] <= 0:
        return jsonify({
            'error': 'Insufficient transaction history or negative savings.',
            'profile': profile
        }), 400
    
    # Generate suggestions for different loan amounts
    # Start from 25% of recommended max, go up to 100% in increments
    suggestions = []
    
    loan_amounts = [
        profile['recommended_max_loan'] * 0.25,
        profile['recommended_max_loan'] * 0.5,
        profile['recommended_max_loan'] * 0.75,
        profile['recommended_max_loan']
    ]
    
    for loan_amount in loan_amounts:
        if loan_amount <= 0:
            continue
        
        rates_breakdown = []
        for rate in [min_rate, (min_rate + max_rate) / 2, max_rate]:
            emi = calculate_emi(loan_amount, rate, tenure)
            rates_breakdown.append({
                'interest_rate_percent': rate,
                'emi_monthly': emi,
                'total_interest': round(emi * tenure - loan_amount, 2),
                'total_repayment': round(emi * tenure, 2),
                'affordable': emi <= profile['affordable_monthly_emi']
            })
        
        suggestions.append({
            'loan_amount': round(loan_amount, 0),
            'tenure_months': tenure,
            'interest_rate_options': rates_breakdown
        })
    
    return jsonify({
        'user_profile': profile,
        'suggestions': suggestions,
        'note': 'Choose a loan amount and interest rate combination. EMI must be <= affordable_monthly_emi for affordability.'
    }), 200


@app.route('/emi-calculator', methods=['POST'])
@jwt_required()
def emi_calculator():
    """
    Direct EMI calculator endpoint.
    Body: {
      "principal": 100000,
      "annual_interest_rate": 10,
      "tenure_months": 60
    }
    Returns detailed EMI breakdown.
    """
    payload = request.get_json(force=True)
    principal = float(payload.get('principal', 0))
    annual_rate = float(payload.get('annual_interest_rate', 0))
    tenure = int(payload.get('tenure_months', 60))
    
    if principal <= 0 or tenure <= 0:
        return jsonify({'error': 'Principal and tenure must be > 0'}), 400
    if annual_rate < 0:
        return jsonify({'error': 'Interest rate cannot be negative'}), 400
    
    emi = calculate_emi(principal, annual_rate, tenure)
    total_repay = emi * tenure
    total_interest = total_repay - principal
    
    return jsonify({
        'principal': principal,
        'annual_interest_rate': annual_rate,
        'monthly_interest_rate': round(annual_rate / 12, 4),
        'tenure_months': tenure,
        'emi_monthly': emi,
        'total_interest': round(total_interest, 2),
        'total_repayment': round(total_repay, 2),
        'breakdown': {
            'principal_component': round(principal / tenure, 2),
            'interest_component_first_month': round(principal * annual_rate / 12 / 100, 2),
            'interest_component_last_month': round((principal - (principal / tenure * (tenure - 1))) * annual_rate / 12 / 100, 2)
        }
    }), 200


if __name__ == "__main__":
    # Render sets PORT environment variable; fall back to 5000 for local dev
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
