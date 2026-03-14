import os
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from services.stock_service import get_stock_suggestions
from services.loan_service import get_loan_suggestions
from services.insurance_service import get_insurance_plans
from services.ai_service import generate_ai_insight
from utils.encryption import encrypt_data, decrypt_data
from utils.transaction_hash import generate_hash

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
CORS(app, resources={r"/*": {"origins": "*"}})

jwt = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})
cache.init_app(app)

# Database connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/finance_db")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client["finance_db"]
    transactions_collection = db["transactions"]
    users_collection = db["users"]
    print("✓ MongoDB connected")
except Exception as e:
    print(f"⚠️  MongoDB error: {e}")
    db = None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "FinTrack API"})

@app.route("/login-google", methods=["POST"])
def login_google():
    data = request.json
    google_user_id = data.get("google_id")
    email = data.get("email")
    name = data.get("name")
    
    if not google_user_id:
        return jsonify({"error": "invalid login"}), 400
    
    if db:
        try:
            existing_user = users_collection.find_one({"google_id": google_user_id})
            if not existing_user:
                users_collection.insert_one({"google_id": google_user_id, "email": email, "name": name})
        except PyMongoError as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    access_token = create_access_token(identity=google_user_id)
    return jsonify({"token": access_token})

@app.route("/sync-transactions", methods=["POST"])
@jwt_required()
@limiter.limit("10 per minute")
def sync_transactions():
    user_id = get_jwt_identity()
    transactions = request.json
    
    if not isinstance(transactions, list):
        return jsonify({"error": "transactions must be an array"}), 400
    
    inserted = 0
    if db:
        for txn in transactions:
            try:
                txn_hash = generate_hash(txn)
                exists = transactions_collection.find_one({"transaction_hash": txn_hash})
                if exists:
                    continue
                
                encrypted_amount = encrypt_data(str(txn["amount"]))
                encrypted_merchant = encrypt_data(txn["merchant"])
                
                transactions_collection.insert_one({
                    "user_id": user_id,
                    "encrypted_amount": encrypted_amount,
                    "encrypted_merchant": encrypted_merchant,
                    "type": txn["type"],
                    "category": txn.get("category", "other"),
                    "date": txn["date"],
                    "transaction_hash": txn_hash
                })
                inserted += 1
            except Exception as e:
                print(f"Transaction error: {e}")
                continue
    
    return jsonify({"message": "transactions synced", "inserted": inserted})

@app.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    result = []
    
    if db:
        try:
            txns = list(transactions_collection.find({"user_id": user_id}))
            for t in txns:
                try:
                    result.append({
                        "amount": float(decrypt_data(t["encrypted_amount"])),
                        "merchant": decrypt_data(t["encrypted_merchant"]),
                        "type": t["type"],
                        "category": t["category"],
                        "date": t["date"]
                    })
                except Exception:
                    continue
        except PyMongoError as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    return jsonify(result)

@app.route("/ai-insights", methods=["POST"])
@jwt_required()
def ai_insights():
    user_id = get_jwt_identity()
    question = request.json.get("question", "Give me a financial health summary")
    parsed_transactions = []
    
    if db:
        try:
            txns = list(transactions_collection.find({"user_id": user_id}))
            for t in txns:
                try:
                    parsed_transactions.append({
                        "amount": float(decrypt_data(t["encrypted_amount"])),
                        "merchant": decrypt_data(t["encrypted_merchant"]),
                        "type": t["type"],
                        "category": t["category"],
                        "date": t["date"]
                    })
                except Exception:
                    continue
        except PyMongoError as e:
            return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    try:
        result = generate_ai_insight(parsed_transactions, question)
    except Exception as e:
        return jsonify({"error": f"AI service error: {str(e)}"}), 502
    
    return jsonify(result)

@app.route("/stock-suggestions", methods=["GET"])
@cache.cached(timeout=3600)
def stock_suggestions():
    try:
        data = get_stock_suggestions()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"Stock service error: {str(e)}"}), 502

@app.route("/loan-suggestions", methods=["POST"])
@jwt_required()
def loan_suggestions():
    data = request.json
    income = data.get("income")
    expenses = data.get("expenses")
    
    if not income or not expenses:
        return jsonify({"error": "income and expenses are required"}), 400
    
    result = get_loan_suggestions(income, expenses)
    return jsonify(result)

@app.route("/insurance-suggestions", methods=["POST"])
@jwt_required()
def insurance_suggestions():
    data = request.json
    age = data.get("age")
    income = data.get("income")
    
    if not age or not income:
        return jsonify({"error": "age and income are required"}), 400
    
    result = get_insurance_plans(age, income)
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
